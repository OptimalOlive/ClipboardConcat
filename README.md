# ClipboardConcat

ClipboardConcat is a Python utility with a graphical user interface that allows you to easily combine text content from multiple files or entire directories. It intelligently respects `.gitignore` rules when processing folders, offers options to add custom suffix instructions, and provides multiple ways to use the aggregated text: copy to clipboard, save to a file, or prepare a temporary file for dragging.

## Features

* **Drag & Drop Interface:** Intuitive drag-and-drop area for files and folders.
* **Recursive Folder Scanning:** Processes text files within dropped folders and their subdirectories.
* **.gitignore Aware:** Intelligently skips files and directories specified in `.gitignore` files when a folder is processed (requires `pathspec` library).
* **Custom Suffix/Instructions:** Option to append custom text (e.g., instructions for an AI) to the end of the combined content.
* **Multiple Output Actions:**
    * Copy to Clipboard: Instantly copy the result.
    * Save to File: Save the result to a chosen file.
    * Prepare Draggable File: Saves the result to a temporary file and reveals it in your file explorer for easy dragging.
* **Informative Status:** Provides feedback on the number of files processed, skipped, ignored, and total lines/characters.
* **Cross-Platform (mostly):** Built with Tkinter, aiming for broad compatibility. File explorer integration for "Prepare Draggable File" is OS-aware.

## Prerequisites

* Python 3.x
* `pip` (Python package installer)

## Dependencies

* **`tkinterdnd2`**: For drag-and-drop functionality in Tkinter.
* **`pyperclip`**: For cross-platform clipboard access.
* **`pathspec`** (Optional but Recommended): For respecting `.gitignore` files. If not installed, `.gitignore` files will be ignored.

## Setup and Installation

1.  **Clone the repository (or download `app.py`):**
    ```bash
    # If you have git:
    # git clone https://your-repo-url/ClipboardConcat.git
    # cd ClipboardConcat
    # Otherwise, just download app.py
    ```

2.  **Create and activate a Python virtual environment (recommended):**
    ```bash
    python -m venv venv
    # On Windows
    venv\Scripts\activate
    # On macOS/Linux
    source venv/bin/activate
    ```

3.  **Install dependencies:**
    Create a `requirements.txt` file with the following content:
    ```
    tkinterdnd2
    pyperclip
    pathspec
    ```
    Then run:
    ```bash
    pip install -r requirements.txt
    ```
    Or install individually:
    ```bash
    pip install tkinterdnd2 pyperclip pathspec
    ```

## Usage

1.  Ensure your virtual environment is activated (if you created one).
2.  Run the application:
    ```bash
    python app.py
    ```
3.  The main window will appear. Drag your text files or project folders onto the designated drop area.
4.  Optionally, type any suffix or instructions into the text box below the drop area. These will be appended to the combined content.
5.  After processing, the status area will update with details (files processed, lines, characters, etc.).
6.  Use the buttons ("Copy to Clipboard", "Save to File...", "Prepare Draggable File") to export the combined text.

## How `.gitignore` Processing Works

When you drop a folder, `ClipboardConcat` (if `pathspec` is installed) will look for `.gitignore` files within that folder and its subdirectories. It aggregates all the rules found and uses them to exclude matching files and directories from being included in the concatenated output. This is very useful for avoiding temporary files, build artifacts, virtual environments (`venv/`, `node_modules/`), and other non-essential content.
