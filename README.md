# ClipboardConcat

A Python tool to concatenate text content from multiple dropped files or all text files within dropped folders directly to the system clipboard.

## Features

* Drag and drop interface for files and folders.
* Recursively scans folders for text files.
* Attempts to read common text file types (e.g., .py, .js, .css, .txt, .md).
* Skips binary/unreadable files.
* Copies all concatenated text to the clipboard.
* Status messages for user feedback.

## Prerequisites

* Python 3.x
* `pip` (Python package installer)
* For Linux: `xclip` or `xsel` is required by the `pyperclip` library for clipboard access (`sudo apt-get install xclip` or `sudo apt-get install xsel`).

## Setup and Installation

1.  **Clone the repository (or download the files):**
    ```bash
    git clone [https://github.com/YourUsername/ClipboardConcat.git](https://github.com/YourUsername/ClipboardConcat.git)
    cd ClipboardConcat
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv venv
    # Windows
    venv\Scripts\activate
    # macOS/Linux
    source venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Usage

1.  Ensure your virtual environment is activated.
2.  Run the application:
    ```bash
    python app.py
    ```
3.  Drag files or folders onto the application window. The combined text content will be copied to your clipboard.

## Dependencies

* `tkinterdnd2`: For drag-and-drop functionality in Tkinter.
* `pyperclip`: For cross-platform clipboard access.

## Contributing (Optional)

Contributions are welcome! Please feel free to submit a pull request or open an issue.

## License (Optional)

This project is licensed under the MIT License - see the LICENSE.md file for details.