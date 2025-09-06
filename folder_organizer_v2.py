import os
import shutil
import hashlib
import logging
import re
import sys
import subprocess
from pathlib import Path
from collections import defaultdict
from tkinter import Tk, filedialog, TclError

# --- Dependency Installation ---
try:
    import inquirer
except ImportError:
    print("Required library 'inquirer' not found. Attempting to install...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "inquirer"])
        print("'inquirer' installed successfully.")
        import inquirer
    except Exception as e:
        print(f"Error: Failed to install 'inquirer'. {e}")
        print("Please install it manually by running: pip install inquirer")
        sys.exit(1)

# --- Script Configuration ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("file_organizer.log"),
        logging.StreamHandler()
    ]
)

def select_folder() -> Path:
    """
    Opens a GUI window using tkinter to select the folder to organize.
    """
    print("Attempting to open the graphical folder selection dialog...")
    try:
        root = Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        
        print("A folder selection window should now be open. It may be behind other windows.")
        folder = filedialog.askdirectory(title="Select Folder to Organize")
        
        root.destroy()

        if folder:
            print(f"Folder selected: {folder}")
            logging.debug(f"Selected folder: {folder}")
            return Path(folder)
        else:
            logging.info("No folder was selected from the dialog.")
            return None
            
    except TclError as e:
        print("\n--- CRITICAL ERROR ---")
        print("Could not open the graphical folder selection window.")
        logging.error(f"Tkinter failed to initialize: {e}")
        return None
    except Exception as e:
        print(f"\nAn unexpected error occurred during folder selection: {e}")
        logging.error(f"An unexpected error occurred in select_folder: {e}")
        return None

def get_directory_stats(folder_path: Path) -> dict:
    """
    Gathers statistics about the directory.
    """
    stats = {"total_files": 0, "total_folders": 0, "total_size": 0}
    try:
        for item in folder_path.rglob("*"):
            if item.is_file():
                stats["total_files"] += 1
                try:
                    stats["total_size"] += item.stat().st_size
                except OSError as e:
                    logging.warning(f"Could not get size of file {item}: {e}")
            elif item.is_dir():
                stats["total_folders"] += 1
    except OSError as e:
        logging.error(f"Could not scan directory {folder_path}: {e}")
    return stats

def human_readable_size(size, decimal_places=2):
    """
    Converts bytes to a human-readable format (KB, MB, GB, TB).
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            break
        size /= 1024.0
    return f"{size:.{decimal_places}f} {unit}"

def get_user_choices(base_folder: Path, category_folders: set) -> (list, list):
    """
    Asks the user which files and folders to skip.
    """
    all_items = [item for item in base_folder.iterdir()]
    files_to_consider = sorted([f.name for f in all_items if f.is_file()])
    folders_to_consider = sorted([f.name for f in all_items if f.is_dir() and f.name not in category_folders])

    if not files_to_consider and not folders_to_consider:
        return [], []

    questions = [
        inquirer.Checkbox('files_to_skip',
                          message="Select files to SKIP (use arrow keys, space to select, enter to confirm)",
                          choices=files_to_consider),
        inquirer.Checkbox('folders_to_skip',
                          message="Select folders to SKIP",
                          choices=folders_to_consider)
    ]
    answers = inquirer.prompt(questions)
    if not answers: # Handle Ctrl+C
        return [], []
    return answers.get('files_to_skip', []), answers.get('folders_to_skip', [])


def compute_hash(fp: Path, chunk_size=65536) -> str:
    h = hashlib.sha256()
    try:
        with fp.open("rb") as f:
            while chunk := f.read(chunk_size):
                h.update(chunk)
        return h.hexdigest()
    except (IOError, OSError) as e:
        logging.error(f"Could not read file {fp} to compute hash: {e}")
        return None


def handle_duplicates(base_folder: Path, category_folders: set) -> int:
    """
    Finds and deletes duplicate files based on hash, ignoring category folders.
    """
    logging.info("Scanning for duplicate files (ignoring destination folders)...")
    hashes = defaultdict(list)
    
    for item in base_folder.rglob('*'):
        # Check if the item is within one of the category folders
        if any(part in category_folders for part in item.relative_to(base_folder).parts):
            continue
        
        if item.is_file():
            file_hash = compute_hash(item)
            if file_hash:
                hashes[file_hash].append(item)

    duplicates_deleted = 0
    for file_paths in hashes.values():
        if len(file_paths) > 1:
            # Prefer to keep files without '(x)' in the name
            originals = [p for p in file_paths if not re.search(r'\(\d+\)', p.stem)]
            if not originals:
                # If all have '(x)' or none do, just keep the first one
                originals.append(file_paths[0])
            
            # All files that are not the chosen original are marked for deletion
            duplicates_to_delete = [p for p in file_paths if p not in originals]

            if duplicates_to_delete:
                logging.info(f"Duplicate found for: {originals[0].name}")
                for dup in duplicates_to_delete:
                    try:
                        dup.unlink()
                        logging.info(f"  - Deleted duplicate: {dup.name}")
                        duplicates_deleted += 1
                    except OSError as e:
                        logging.error(f"Could not delete duplicate file {dup}: {e}")
    
    return duplicates_deleted


def ensure_folder_exists(folder: Path) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    logging.debug(f"Ensured folder exists: {folder}")


def get_target_filename(src: Path) -> str:
    if src.suffix.lower() == ".pdf":
        stem, ext = os.path.splitext(src.name)
        return f"{stem.title()}{ext.lower()}"
    return src.name


def move_and_rename_file(src: Path, dest_folder: Path) -> bool:
    src = src.resolve()
    dest_folder = dest_folder.resolve()
    base = get_target_filename(src)
    target = dest_folder / base
    logging.debug(f"Processing file: {src} -> {target}")

    if target.exists():
        logging.debug(f"Conflict: {target} exists")
        if compute_hash(target) == compute_hash(src):
            logging.info(f"Duplicate of '{target.name}' found. Deleting source: {src.name}")
            src.unlink()
            return False
        
        stem, ext = os.path.splitext(base)
        counter = 1
        while True:
            candidate = dest_folder / f"{stem}_{counter}{ext}"
            if not candidate.exists():
                target = candidate
                break
            counter += 1
    
    try:
        shutil.move(str(src), str(target))
        logging.debug(f"Moved file to: {target}")
        return True
    except (shutil.Error, OSError) as e:
        logging.error(f"Could not move file {src} to {target}: {e}")
        return False


def move_folder(src: Path, dest_parent: Path) -> bool:
    src = src.resolve()
    dest_parent = dest_parent.resolve()
    target = dest_parent / src.name

    if target.exists():
        logging.debug(f"Folder conflict: {target}")
        counter = 1
        while (dest_parent / f"{src.name}_{counter}").exists():
            counter += 1
        target = dest_parent / f"{src.name}_{counter}"
    
    try:
        shutil.move(str(src), str(target))
        logging.debug(f"Moved folder to: {target}")
        return True
    except (shutil.Error, OSError) as e:
        logging.error(f"Could not move folder {src} to {target}: {e}")
        return False


def refine_sorting(base_folder: Path, summary: dict):
    others_folder = base_folder / "10 - OTHERS"
    coding_folder = base_folder / "7 - CODING"
    refine_exts = {".json", ".tsx", ".ts", ".yaml", ".yml"}
    if others_folder.exists() and coding_folder.exists():
        for item in list(others_folder.iterdir()):
            if item.is_file() and item.suffix.lower() in refine_exts:
                logging.debug(f"Refining: moving {item.name} from 10 - OTHERS to 7 - CODING")
                if move_and_rename_file(item, coding_folder):
                    summary['files_moved'] += 1


def main():
    base_folder = select_folder()
    if not base_folder:
        print("No folder selected or GUI failed to open. Exiting.")
        return

    folders = {
        "1 - ARCHIVES": [".7z", ".bz2", ".dmp", ".gz", ".iso", ".rar", ".tar", ".torrent", ".xz", ".zip"],
        "2 - DOCUMENTS": [".bib", ".csv", ".dic", ".doc", ".docx", ".epub", ".htm", ".md", ".pages", ".ppt", ".pptx", ".ps", ".ris", ".ttl", ".txt", ".xls", ".xlsx"],
        "3 - IMAGES": [".bmp", ".gif", ".heic", ".jpeg", ".jpg", ".png", ".svg", ".tiff", ".webp"],
        "4 - PDFs": [".pdf"],
        "5 - VIDEOS": [".avi", ".flv", ".mkv", ".mov", ".mp4", ".wmv"],
        "6 - FOLDERS": [],
        "7 - CODING": [".bat", ".c", ".cpp", ".css", ".gexf", ".har", ".html", ".java", ".js", ".json", ".php", ".ps1", ".py", ".sh", ".sqlite3", ".ts", ".tsx", ".xml", ".yaml", ".yml", ".ipynb"],
        "8 - INSTALLERS & APPLICATIONS": [".apk", ".bin", ".dll", ".dmg", ".exe", ".jar", ".msi"],
        "9 - SECURITY": [".cer"],
        "10 - OTHERS": []
    }
    defined_categories = set(folders.keys())

    # --- Main Application Loop ---
    while True:
        # Clear screen for a cleaner interface on each loop
        os.system('cls' if os.name == 'nt' else 'clear')

        # Gather and display fresh statistics each time the menu is shown
        stats = get_directory_stats(base_folder)
        print(f"--- Directory Statistics for: {base_folder.name} ---")
        print(f"Total Files: {stats['total_files']}")
        print(f"Total Folders: {stats['total_folders']}")
        print(f"Total Size: {human_readable_size(stats['total_size'])}")
        print("--------------------------------------------------\n")

        summary = defaultdict(int)

        questions = [
            inquirer.List('action',
                          message="What would you like to do?",
                          choices=['Organize Files and Folders', 'Find and Delete Duplicates', 'Do Both', 'Exit'],
                          ),
        ]
        answers = inquirer.prompt(questions)

        if not answers or answers['action'] == 'Exit':
            print("Exiting.")
            break
        
        action_choice = answers['action']

        if 'Duplicate' in action_choice or 'Both' in action_choice:
            summary['duplicates_deleted'] = handle_duplicates(base_folder, defined_categories)

        if 'Organize' in action_choice or 'Both' in action_choice:
            files_to_skip, folders_to_skip = get_user_choices(base_folder, defined_categories)
            summary['files_skipped'] = len(files_to_skip)
            summary['folders_skipped'] = len(folders_to_skip)

            for folder_name in folders:
                ensure_folder_exists(base_folder / folder_name)

            for item in list(base_folder.iterdir()):
                if item.name in files_to_skip or item.name in folders_to_skip or item.name in defined_categories:
                    continue

                if item.is_file():
                    ext_lower = item.suffix.lower()
                    if "ipynb" in item.name.lower() and ext_lower != ".ipynb":
                        ext_lower = ".ipynb"
                    
                    destination = None
                    for folder_name, exts in folders.items():
                        if exts and ext_lower in {ext.lower() for ext in exts}:
                            destination = base_folder / folder_name
                            break
                    if not destination:
                        destination = base_folder / "10 - OTHERS"
                    
                    if move_and_rename_file(item, destination):
                        summary['files_moved'] += 1

            for item in list(base_folder.iterdir()):
                if item.is_dir() and item.name not in defined_categories and item.name not in folders_to_skip:
                    dest = base_folder / "6 - FOLDERS"
                    ensure_folder_exists(dest)
                    if move_folder(item, dest):
                        summary['folders_moved'] += 1
            
            refine_sorting(base_folder, summary)

        print("\n--- Action Summary ---")
        print(f"Files Moved: {summary['files_moved']}")
        print(f"Folders Moved: {summary['folders_moved']}")
        print(f"Duplicate Files Deleted: {summary['duplicates_deleted']}")
        print(f"Files Skipped: {summary['files_skipped']}")
        print(f"Folders Skipped: {summary['folders_skipped']}")
        print("----------------------")
        
        input("Press Enter to continue...")


if __name__ == "__main__":
    main()
