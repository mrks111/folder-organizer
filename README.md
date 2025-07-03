# Smart Folder Organizer Script

This Python script helps you automatically organize a messy folder by sorting files into predefined categories. It uses a graphical user interface (GUI) to select the target folder, making it easy to use.

The script is designed to be safe and intelligent, featuring duplicate file detection, smart conflict resolution, and special handling for certain file types.

## Key Features

*   **GUI for Folder Selection**: No need to edit the script to specify a folder path. A simple dialog box pops up for you to choose.
*   **Categorization by File Type**: Sorts files into specific folders like `1 - ARCHIVES`, `2 - DOCUMENTS`, `3 - IMAGES`, etc., based on their extensions.
*   **Duplicate File Detection**: Uses SHA256 hashing to identify true duplicate files (even with different names). If a duplicate is found, the new file is deleted to avoid clutter.
*   **Smart Conflict Resolution**: If two different files have the same name, the script renames the incoming file by appending a number (e.g., `report_1.pdf`).
*   **Organizes Sub-folders**: Moves any existing sub-folders (that aren't category folders) into a dedicated `6 - FOLDERS` directory to keep the root clean.
*   **Special PDF Naming**: Automatically reformats PDF filenames to be Title-Cased for consistency (e.g., `my annual report.pdf` becomes `My Annual Report.pdf`).
*   **Detailed Logging**: Provides real-time feedback in the console about every action it takes, from moving files to detecting duplicates.

## Prerequisites

*   **Python 3.x**: The script is written in Python 3.
*   **Tkinter**: This is the standard GUI library for Python. It's usually included with Python installations on Windows and macOS. On some Linux distributions, you may need to install it separately:
    ```bash
    # For Debian/Ubuntu
    sudo apt-get install python3-tk
    ```

## How to Use

1.  **Save the Script**: Save the code as a Python file (e.g., `organizer.py`).
2.  **Run the Script**: Open a terminal or command prompt, navigate to the directory where you saved the file, and run it:
    ```bash
    python organizer.py
    ```
3.  **Select a Folder**: A dialog box will appear. Navigate to and select the folder you want to organize.
4.  **Let it Run**: The script will process the selected folder. You can monitor its progress in the terminal window. Once it's finished, your folder will be neatly organized.

## The Organized Folder Structure

The script will create the following folders in your selected directory and sort files into them accordingly:

*   **`1 - ARCHIVES`**: `.zip`, `.rar`, `.7z`, `.tar`, `.gz`, `.bz2`
*   **`2 - DOCUMENTS`**: `.doc`, `.ris`, `.ttl`, `.docx`, `.txt`, `.xlsx`, `.ppt`, `.csv`, `.pptx`, `.md`
*   **`3 - IMAGES`**: `.jpeg`, `.jpg`, `.png`, `.gif`, `.bmp`, `.heic`, `.tiff`, `.svg`
*   **`4 - PDFs`**: `.pdf`
*   **`5 - VIDEOS`**: `.mp4`, `.mov`, `.avi`, `.mkv`, `.flv`, `.wmv`
*   **`6 - FOLDERS`**: All sub-folders that are not part of the categories above will be moved here.
*   **`7 - CODING`**: `.py`, `.java`, `.cpp`, `.c`, `.html`, `.css`, `.js`, `.php`, `.tsx`, `.ts`, `.yaml`, `.yml`, `.json`
*   **`8 - INSTALLERS & APPLICATIONS`**: `.exe`
*   **`9 - OTHERS`**: Any file type that does not match the categories above.

## How It Works: A Deeper Look

1.  **Initialization**: The script defines the category folders and their associated file extensions. It then creates these folders in the user-selected directory.
2.  **File Processing**:
    *   It iterates through all items in the root of the selected folder.
    *   For each file, it checks the extension and finds the matching category folder.
    *   If no category matches, it's destined for `9 - OTHERS`.
    *   The file is then passed to the `move_and_rename_file` function.
3.  **Duplicate & Conflict Handling (`move_and_rename_file`)**:
    *   **If the destination file doesn't exist**: The file is moved and (if it's a PDF) renamed.
    *   **If a file with the same name exists**:
        *   The script calculates the SHA256 hash of both the source file and the existing destination file.
        *   If the hashes match, the files are identical. The script logs this and **deletes the source file**, preventing duplicates.
        *   If the hashes are different, it's a name collision. The script appends `_1`, `_2`, etc., to the source filename until a unique name is found, and then moves the file.
4.  **Folder Processing (`move_folder`)**: After processing all files, the script iterates through the items again. Any sub-directory that isn't a main category folder (e.g., `1 - ARCHIVES`) is moved into the `6 - FOLDERS` directory. This includes handling name conflicts by appending `_1`, `_2`, etc.
5.  **Refinement Pass (`refine_sorting`)**: As a final step, the script checks the `9 - OTHERS` folder for certain coding-related files (`.json`, `.tsx`, etc.) that might have ended up there and moves them to the more appropriate `7 - CODING` folder.

## Customization

You can easily customize the folder categories and the file types associated with them by editing the `folders` dictionary within the `main()` function of the script. For example, to add `.epub` to documents and create a new category for music, you could modify it like this:

```python
# Edit this dictionary to change categories or file types
folders = {
    "1 - ARCHIVES": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"],
    "2 - DOCUMENTS": [".doc", ".ris", ".ttl", ".docx", ".txt", ".xlsx", ".ppt", ".csv", ".pptx", ".md", ".epub"], # Added .epub
    "3 - IMAGES": [".jpeg", ".jpg", ".png", ".gif", ".bmp", ".heic", ".tiff", ".svg"],
    "4 - PDFs": [".pdf"],
    "5 - VIDEOS": [".mp4", ".mov", ".avi", ".mkv", ".flv", ".wmv"],
    "6 - FOLDERS": [],
    "7 - CODING": [".py", ".java", ".cpp", ".c", ".html", ".css", ".js", ".php",
                     ".tsx", ".ts", ".yaml", ".yml", ".json"],
    "8 - MUSIC": [".mp3", ".wav", ".flac"], # New category
    "9 - INSTALLERS & APPLICATIONS": [".exe"],
    "10 - OTHERS": [] # Renumber subsequent folders
}
