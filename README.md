# Smart Folder Organizer

A Python script that automatically organizes a messy folder by sorting files into predefined categories. Uses a GUI dialog for folder selection and is built to be fast, safe, and resilient — it won't get stuck on locked files, system executables, or slow drives.

---

## Key Features

- **GUI Folder Selection** — a dialog box opens so you never have to edit the script to specify a path.
- **Interactive Skip List** — choose which files and folders to leave untouched before the script runs.
- **Category Sorting** — files are sorted into numbered folders (`1 - ARCHIVES`, `2 - DOCUMENTS`, etc.) based on their extension.
- **Duplicate Detection** — uses SHA-256 hashing to identify identical files, even if they have different names. True duplicates are deleted; different files with the same name are renamed with a counter suffix.
- **Size Pre-Filtering** — before hashing anything, files are grouped by byte size. Files with a unique size cannot be duplicates, so they are skipped entirely. This eliminates ~90% of hashing work on typical folders.
- **Parallel Hashing** — duplicate candidates are hashed concurrently across 8 threads, giving a near-linear speedup on I/O-bound workloads.
- **Per-File Hash Timeout** — any file that takes longer than 5 seconds to hash (locked executables, system files, slow network shares) is automatically skipped and logged. The script never hangs.
- **Folder Organization** — sub-folders that are not category folders are moved into `6 - FOLDERS`.
- **PDF Title-Casing** — PDF filenames are automatically reformatted to Title Case (`my annual report.pdf` → `My Annual Report.pdf`).
- **Refinement Pass** — after sorting, coding-adjacent files (`.json`, `.ts`, `.tsx`, `.yaml`, `.yml`) that ended up in `10 - OTHERS` are moved to `7 - CODING`.
- **Detailed Logging** — every action is logged to both the console and `file_organizer.log`, including skips, timeouts, and deletions.

---

## Requirements

- **Python 3.10+** (uses the walrus operator and `str | None` union syntax)
- **Tkinter** — included with Python on Windows and macOS. On Linux:
  ```bash
  sudo apt-get install python3-tk   # Debian / Ubuntu
  sudo dnf install python3-tkinter  # Fedora
  ```
- **inquirer** — installed automatically on first run if missing.

---

## Usage

```bash
python file_organizer.py
```

1. A folder selection dialog opens — pick the folder you want to organize.
2. Choose an action from the menu:
   - **Organize Files and Folders**
   - **Find and Delete Duplicates**
   - **Do Both**
3. If organizing, select any files or folders you want to skip.
4. The script runs and prints a summary when done.

---

## Output Folder Structure

| Folder | Extensions |
|---|---|
| `1 - ARCHIVES` | `.7z` `.bz2` `.dmp` `.gz` `.iso` `.rar` `.tar` `.torrent` `.xz` `.zip` |
| `2 - DOCUMENTS` | `.bib` `.csv` `.dic` `.doc` `.docx` `.epub` `.htm` `.md` `.pages` `.ppt` `.pptx` `.ps` `.ris` `.ttl` `.txt` `.xls` `.xlsx` |
| `3 - IMAGES` | `.bmp` `.gif` `.heic` `.jpeg` `.jpg` `.png` `.svg` `.tiff` `.webp` |
| `4 - PDFs` | `.pdf` |
| `5 - VIDEOS` | `.avi` `.flv` `.mkv` `.mov` `.mp4` `.wmv` |
| `6 - FOLDERS` | *(sub-folders)* |
| `7 - CODING` | `.bat` `.c` `.cpp` `.css` `.gexf` `.har` `.html` `.ipynb` `.java` `.js` `.json` `.php` `.ps1` `.py` `.sh` `.sqlite3` `.ts` `.tsx` `.xml` `.yaml` `.yml` |
| `8 - INSTALLERS & APPLICATIONS` | `.apk` `.bin` `.dll` `.dmg` `.exe` `.jar` `.msi` |
| `9 - SECURITY` | `.cer` |
| `10 - OTHERS` | *(anything not matched above)* |

---

## How It Works

### Duplicate Detection (when selected)

**Phase 1 — Size grouping**
All files are grouped by byte size. A file with a size no other file shares is guaranteed to be unique and is excluded from hashing immediately. This single step typically eliminates 70–95% of the work.

**Phase 2 — Parallel hashing**
Remaining candidates are hashed in parallel using a thread pool (default: 8 workers). Each hash has a hard 5-second timeout — files that would have caused the script to hang indefinitely are skipped and logged with a `[TIMEOUT]` marker instead.

Files with identical hashes are duplicates. The script keeps the version without a `(x)` suffix in its name (i.e., the presumed original) and deletes the rest.

### File Organization (when selected)

1. Category folders are created if they don't already exist.
2. The script iterates the root of the selected folder. Each file is matched to a category by extension and moved. Unmatched files go to `10 - OTHERS`.
3. Any remaining sub-folders (not category folders) are moved into `6 - FOLDERS`.
4. A refinement pass checks `10 - OTHERS` and promotes coding-adjacent files to `7 - CODING`.

### Conflict Resolution

When a file is moved to a destination where a file of the same name already exists:
- If both files are **identical** (matching hash): the incoming file is deleted.
- If they are **different**: the incoming file is renamed with a counter suffix (`report_1.pdf`, `report_2.pdf`, etc.).

---

## Tunable Constants

Three constants at the top of the script control performance behaviour:

```python
HASH_CHUNK_SIZE = 524288   # Bytes read per I/O call (default: 512KB)
HASH_TIMEOUT_SEC = 5       # Max seconds to wait per file hash
MAX_HASH_WORKERS = 8       # Parallel hashing threads
```

Increase `MAX_HASH_WORKERS` on machines with fast SSDs and many cores. Lower `HASH_TIMEOUT_SEC` if you want to be more aggressive about skipping slow files.

---

## Customization

Edit the `folders` dictionary inside `main()` to add, remove, or rename categories:

```python
folders = {
    "1 - ARCHIVES": [".zip", ".rar", ".7z", ".tar", ".gz"],
    "2 - DOCUMENTS": [".doc", ".docx", ".txt", ".pdf", ".epub"],  # added .epub
    # ... other categories ...
    "8 - MUSIC": [".mp3", ".wav", ".flac"],   # new category
    "9 - INSTALLERS & APPLICATIONS": [".exe", ".msi"],
    "10 - OTHERS": []
}
```

The script self-skips automatically — you don't need to add `file_organizer.py` to the skip list manually.

---

## Log File

All actions are written to `file_organizer.log` in the directory where the script is run. Useful log markers:

| Marker | Meaning |
|---|---|
| `[SKIP]` | File could not be read (permission denied, etc.) |
| `[TIMEOUT]` | File hash exceeded the timeout limit |
| `[ERROR]` | Unexpected error during hashing |
