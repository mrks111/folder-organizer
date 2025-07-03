import os, shutil, hashlib, logging, re
from pathlib import Path
from tkinter import Tk, filedialog

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

def select_folder() -> Path:
    root = Tk()
    root.withdraw()
    folder = filedialog.askdirectory(title="Select Folder to Organize")
    if folder:
        logging.debug(f"Selected folder: {folder}")
        return Path(folder)
    logging.debug("No folder selected")
    return None

def compute_hash(fp: Path, chunk_size=65536) -> str:
    h = hashlib.sha256()
    with fp.open("rb") as f:
        while chunk := f.read(chunk_size):
            h.update(chunk)
    return h.hexdigest()

def ensure_folder_exists(folder: Path) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    logging.debug(f"Ensured folder exists: {folder}")

def get_target_filename(src: Path) -> str:
    # Properize PDFs: title-case the stem, lowercase extension.
    if src.suffix.lower() == ".pdf":
        stem, ext = os.path.splitext(src.name)
        return f"{stem.title()}{ext.lower()}"
    return src.name

def move_and_rename_file(src: Path, dest_folder: Path) -> None:
    src = src.resolve()
    dest_folder = dest_folder.resolve()
    base = get_target_filename(src)
    target = dest_folder / base
    logging.debug(f"Processing file: {src} -> {target}")
    if target.exists():
        logging.debug(f"Conflict: {target} exists")
        if compute_hash(target) == compute_hash(src):
            logging.debug("Duplicate detected; removing source")
            src.unlink()
            return
        stem, ext = os.path.splitext(base)
        counter = 1
        while True:
            candidate = dest_folder / f"{stem}_{counter}{ext}"
            if candidate.exists():
                if compute_hash(candidate) == compute_hash(src):
                    logging.debug("Duplicate candidate found; removing source")
                    src.unlink()
                    return
                counter += 1
            else:
                target = candidate
                break
    shutil.move(str(src), str(target))
    logging.debug(f"Moved file to: {target}")

def move_folder(src: Path, dest_parent: Path) -> None:
    src = src.resolve()
    dest_parent = dest_parent.resolve()
    target = dest_parent / src.name  # Retain original name.
    logging.debug(f"Processing folder: {src} -> {target}")
    if target.exists():
        logging.debug(f"Folder conflict: {target}")
        counter = 1
        while (dest_parent / f"{src.name}_{counter}").exists():
            counter += 1
        target = dest_parent / f"{src.name}_{counter}"
    shutil.move(str(src), str(target))
    logging.debug(f"Moved folder to: {target}")

def refine_sorting(base_folder: Path) -> None:
    # Move coding-related files from "9 - OTHERS" to "7 - CODING"
    others_folder = base_folder / "9 - OTHERS"
    coding_folder = base_folder / "7 - CODING"
    refine_exts = {".json", ".tsx", ".ts", ".yaml", ".yml"}
    if others_folder.exists():
        for item in list(others_folder.iterdir()):
            if item.is_file() and item.suffix.lower() in refine_exts:
                logging.debug(f"Refining: moving {item.name} from 9 - OTHERS to 7 - CODING")
                move_and_rename_file(item, coding_folder)

def main():
    base_folder = select_folder()
    if not base_folder:
        return

    # Define category folders.
    folders = {
        "1 - ARCHIVES": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"],
        "2 - DOCUMENTS": [".doc", ".ris", ".ttl", ".docx", ".txt", ".xlsx", ".ppt", ".csv", ".pptx", ".md"],
        "3 - IMAGES": [".jpeg", ".jpg", ".png", ".gif", ".bmp", ".heic", ".tiff", ".svg"],
        "4 - PDFs": [".pdf"],
        "5 - VIDEOS": [".mp4", ".mov", ".avi", ".mkv", ".flv", ".wmv"],
        "6 - FOLDERS": [],
        "7 - CODING": [".py", ".java", ".cpp", ".c", ".html", ".css", ".js", ".php",
                         ".tsx", ".ts", ".yaml", ".yml", ".json"],
        "8 - INSTALLERS & APPLICATIONS": [".exe"],
        "9 - OTHERS": []
    }

    # Create all category folders.
    for folder_name in folders:
        ensure_folder_exists(base_folder / folder_name)
    defined_categories = set(folders.keys())

    # Process files.
    for item in list(base_folder.iterdir()):
        if item.is_file():
            destination = None
            for folder_name, exts in folders.items():
                if exts and item.suffix.lower() in {ext.lower() for ext in exts}:
                    destination = base_folder / folder_name
                    break
            if not destination:
                destination = base_folder / "9 - OTHERS"
            move_and_rename_file(item, destination)

    # Process directories not matching category names.
    for item in list(base_folder.iterdir()):
        if item.is_dir() and item.name not in defined_categories:
            dest = base_folder / "6 - FOLDERS"
            ensure_folder_exists(dest)
            move_folder(item, dest)
        else:
            logging.debug(f"Preserving category folder: {item.name}")

    refine_sorting(base_folder)

if __name__ == "__main__":
    main()