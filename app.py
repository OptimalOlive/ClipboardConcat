import tkinter as tk
from tkinterdnd2 import DND_FILES, TkinterDnD
import pyperclip
import os

# --- Configuration ---
# Add or remove extensions if you want to be more specific
# If empty, it will try to read all files (and skip non-text ones)
# For this program, we'll attempt to read all files dropped
# and rely on error handling for binary files.
# ALLOWED_EXTENSIONS = ['.txt', '.py', '.js', '.css', '.html', '.json', '.md']

class TextCollectorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Text File Collector")
        self.root.geometry("500x400")

        self.drop_target_label = tk.Label(
            self.root,
            text="Drag and drop text files or folders here",
            pady=20,
            padx=20,
            relief=tk.RIDGE,
            bd=2,
            font=("Arial", 12)
        )
        self.drop_target_label.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)

        # Register the label as a drop target
        self.drop_target_label.drop_target_register(DND_FILES)
        self.drop_target_label.dnd_bind('<<Drop>>', self.on_drop)

        self.status_label = tk.Label(self.root, text="", pady=10, font=("Arial", 10))
        self.status_label.pack(fill=tk.X, padx=10)

    def on_drop(self, event):
        self.status_label.config(text="Processing...")
        self.root.update_idletasks() # Update GUI to show processing message

        dropped_items_str = event.data
        # The event.data can sometimes be a string of multiple paths enclosed in braces {}
        # or a single path. We need to parse it carefully.
        if not dropped_items_str:
            self.status_label.config(text="No items dropped.")
            return

        # Clean up the string: remove braces if present
        if dropped_items_str.startswith('{') and dropped_items_str.endswith('}'):
            dropped_items_str = dropped_items_str[1:-1]
            # Paths might be separated by spaces but can also contain spaces themselves.
            # A common way TkinterDnD returns multiple paths is space-separated if they don't have spaces,
            # or enclosed in {} and then potentially quoted if they have spaces.
            # The most robust way is to ask the system for the actual list if possible,
            # but TkinterDnD usually gives a string.
            # We'll split by ' ' and then check existence, which is not perfect for paths with spaces
            # if not individually quoted.
            # A more robust way for TkinterDnD is to handle one item at a time if it gives them like that
            # or expect them to be properly escaped/quoted if multiple.
            # For now, let's assume paths are either single or, if multiple, are separable in a way
            # that splitting by " " and then re-joining parts that form a valid path works,
            # or that paths with spaces are individually braced (though less common for DND_FILES).
            # A simpler approach for multiple files is often that event.data is one path string at a time.
            # Let's assume event.data is a single path or multiple paths separated by a known delimiter
            # if the library wraps them. TkinterDnD usually provides one path string in event.data,
            # even if multiple files are selected and dropped from some file explorers.
            # If it's a string list like "{path1} {path2}", we need to split carefully.
            # Let's try splitting by spaces first and then re-construct paths that might contain spaces.

        paths = self.parse_paths(dropped_items_str)

        all_text_content = []
        files_processed_count = 0
        files_skipped_count = 0

        for item_path in paths:
            if not os.path.exists(item_path): # Skip if path doesn't resolve well
                self.status_label.config(text=f"Skipping invalid path: {item_path[:50]}...")
                self.root.update_idletasks()
                continue

            if os.path.isfile(item_path):
                content, read_success = self.read_file_content(item_path)
                if read_success:
                    all_text_content.append(f"\n\n--- Content from: {os.path.basename(item_path)} ---\n")
                    all_text_content.append(content)
                    files_processed_count += 1
                else:
                    files_skipped_count +=1
            elif os.path.isdir(item_path):
                self.status_label.config(text=f"Scanning folder: {item_path[:50]}...")
                self.root.update_idletasks()
                for root_dir, _, filenames in os.walk(item_path):
                    for filename in filenames:
                        file_path = os.path.join(root_dir, filename)
                        content, read_success = self.read_file_content(file_path)
                        if read_success:
                            all_text_content.append(f"\n\n--- Content from: {os.path.relpath(file_path, item_path)} ---\n")
                            all_text_content.append(content)
                            files_processed_count += 1
                        else:
                            files_skipped_count += 1
        
        if all_text_content:
            combined_text = "".join(all_text_content)
            try:
                pyperclip.copy(combined_text)
                self.status_label.config(text=f"Copied content of {files_processed_count} file(s) to clipboard. {files_skipped_count} file(s) skipped.")
            except pyperclip.PyperclipException as e:
                self.status_label.config(text=f"Error copying to clipboard: {e}")
                # Offer to save to a file as a fallback
                self.save_to_file(combined_text)

        elif files_skipped_count > 0 and files_processed_count == 0:
            self.status_label.config(text=f"All {files_skipped_count} file(s) dropped were skipped (likely binary or unreadable).")
        else:
            self.status_label.config(text="No text files found or processed from the dropped items.")

    def parse_paths(self, paths_string):
        """
        Parses the string data from the drop event into a list of paths.
        TkinterDnD can return paths in different formats, sometimes space-separated,
        sometimes with curly braces. This function tries to handle common cases.
        """
        # Remove leading/trailing whitespace and braces
        paths_string = paths_string.strip()
        if paths_string.startswith('{') and paths_string.endswith('}'):
            paths_string = paths_string[1:-1]

        # This is a tricky part. If paths have spaces, simple splitting by ' ' won't work.
        # TkinterDnD might provide paths like:
        # 'C:/path1/file one.txt C:/path2/file_two.txt'
        # or '{C:/path1/file one.txt} {C:/path2/file_two.txt}'
        # A more robust method might be needed if simple split fails.
        # For now, we assume that if there are multiple paths, they are either
        # space-separated (if no spaces in paths) or individually braced/quoted.
        # Let's try a more robust split if paths could be quoted or contain spaces.
        # This is a heuristic:
        
        # If there are no '{' in the string, it's likely space-separated or a single path
        if '{' not in paths_string:
            # This won't handle paths with spaces correctly if multiple are dropped and not quoted
            # But often TkinterDnD gives one path at a time, or system handles quoting.
            # If it's a single path with spaces, it should be fine.
            # If multiple paths with spaces, this heuristic might fail.
            # Example: "C:/My Documents/file a.txt" C:/My Documents/file b.txt"
            # A common scenario is one path string, even for multiple files if the OS/TkinterDnD packs them.
            # Let's assume paths are separated by a null character or are single.
            # However, event.data is usually space separated if no spaces in names, or one path.
            
            # Simple split for now; might need refinement based on actual TkinterDnD behavior on specific OS
            potential_paths = paths_string.split(' ') 
            actual_paths = []
            current_path = ""
            for part in potential_paths:
                if current_path: # try to re-assemble paths with spaces
                    test_path = current_path + " " + part
                else:
                    test_path = part
                
                if os.path.exists(test_path):
                    actual_paths.append(test_path)
                    current_path = ""
                elif os.path.exists(part) and not current_path: # if 'part' itself is a path
                     actual_paths.append(part)
                     current_path = ""
                else: # continue assembling
                    if current_path:
                        current_path += " " + part
                    else:
                        current_path = part
            if current_path and os.path.exists(current_path): # add any remaining path
                actual_paths.append(current_path)
            
            if not actual_paths and os.path.exists(paths_string): # If splitting failed, maybe it's a single path
                return [paths_string]
            return actual_paths
        else:
            # Handle cases like "{path one with spaces} {path two with spaces}"
            import re
            paths = []
            # Find items enclosed in {} or non-space sequences
            for match in re.finditer(r'\{([^{}]*?)\}|([^\s]+)', paths_string):
                if match.group(1): # Content from {}
                    paths.append(match.group(1))
                elif match.group(2): # Non-space sequence
                    paths.append(match.group(2))
            
            # Verify paths
            verified_paths = [p for p in paths if os.path.exists(p)]
            if not verified_paths and os.path.exists(paths_string): # Fallback if parsing failed
                 return [paths_string]
            return verified_paths


    def read_file_content(self, file_path):
        # if ALLOWED_EXTENSIONS:
        #     _, ext = os.path.splitext(file_path)
        #     if ext.lower() not in ALLOWED_EXTENSIONS:
        #         # print(f"Skipping (extension not allowed): {file_path}")
        #         return None, False
        try:
            with open(file_path, 'r', encoding='utf-8', errors='strict') as f:
                return f.read(), True
        except UnicodeDecodeError:
            # print(f"Skipping (not a readable UTF-8 text file): {file_path}")
            return None, False # Likely a binary file or different encoding
        except IOError as e:
            # print(f"Skipping (IOError: {e}): {file_path}")
            return None, False # File not found, no permission, etc.
        except Exception as e:
            # print(f"Skipping (Error: {e}): {file_path}")
            return None, False # Other errors


    def save_to_file(self, content):
        try:
            from tkinter import filedialog
            filepath = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
                title="Save collected text as..."
            )
            if filepath:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.status_label.config(text=f"Content saved to {os.path.basename(filepath)}")
            else:
                self.status_label.config(text="Clipboard copy failed. Save cancelled.")
        except Exception as e:
            self.status_label.config(text=f"Failed to save file: {e}")


if __name__ == '__main__':
    # TkinterDnD.Tk() is used instead of tk.Tk() for drag & drop
    root = TkinterDnD.Tk() 
    app = TextCollectorApp(root)
    root.mainloop()