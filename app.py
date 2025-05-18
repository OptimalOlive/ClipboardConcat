import tkinter as tk
from tkinterdnd2 import DND_FILES, TkinterDnD
import pyperclip
import os

class TextCollectorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ClipboardConcat")
        self.root.geometry("600x550")

        # Frame for Instructions Input
        instructions_frame = tk.Frame(self.root)
        instructions_frame.pack(pady=(10, 5), padx=10, fill=tk.X)

        instructions_label = tk.Label(
            instructions_frame,
            text="Custom Suffix/Instructions (optional, added at the end):",
            font=("Arial", 10)
        )
        instructions_label.pack(side=tk.LEFT, anchor='w')

        self.instructions_text_widget = tk.Text(
            self.root,
            height=4,
            pady=5,
            padx=5,
            relief=tk.RIDGE,
            bd=1,
            font=("Arial", 10),
            wrap=tk.WORD
        )
        self.instructions_text_widget.pack(pady=(0, 10), padx=10, fill=tk.X)
        # Add a scrollbar to the instructions text widget (optional, but good for longer text)
        # instructions_scrollbar = tk.Scrollbar(self.instructions_text_widget, command=self.instructions_text_widget.yview)
        # self.instructions_text_widget['yscrollcommand'] = instructions_scrollbar.set
        # instructions_scrollbar.pack(side=tk.RIGHT, fill=tk.Y) # Requires careful packing if used

        self.drop_target_label = tk.Label(
            self.root,
            text="Drag and drop text files or folders here",
            pady=20,
            padx=20,
            relief=tk.GROOVE,
            bd=2,
            font=("Arial", 12)
        )
        self.drop_target_label.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

        self.drop_target_label.drop_target_register(DND_FILES)
        self.drop_target_label.dnd_bind('<<Drop>>', self.on_drop)

        self.status_label = tk.Label(self.root, text="Ready.", pady=10, font=("Arial", 10), wraplength=580)
        self.status_label.pack(fill=tk.X, padx=10, pady=(5,10))

    def on_drop(self, event):
        self.status_label.config(text="Processing...")
        self.root.update_idletasks()

        dropped_items_str = event.data
        if not dropped_items_str:
            self.status_label.config(text="No items dropped.")
            return

        paths = self.parse_paths(dropped_items_str)
        if not paths:
            self.status_label.config(text="Could not parse dropped item paths.")
            return

        collected_file_contents = []
        files_processed_count = 0
        files_skipped_count = 0

        for item_path in paths:
            if not os.path.exists(item_path):
                self.status_label.config(text=f"Skipping invalid path: {item_path[:70]}...")
                self.root.update_idletasks()
                continue

            if os.path.isfile(item_path):
                content, read_success = self.read_file_content(item_path)
                if read_success:
                    # Add a leading newline if this is not the first piece of content
                    if collected_file_contents:
                         collected_file_contents.append("\n\n")
                    collected_file_contents.append(f"--- Content from: {os.path.basename(item_path)} ---\n")
                    collected_file_contents.append(content)
                    files_processed_count += 1
                else:
                    files_skipped_count +=1
            elif os.path.isdir(item_path):
                self.status_label.config(text=f"Scanning folder: {item_path[:70]}...")
                self.root.update_idletasks()
                for root_dir, _, filenames in os.walk(item_path):
                    for filename in filenames:
                        file_path = os.path.join(root_dir, filename)
                        content, read_success = self.read_file_content(file_path)
                        if read_success:
                            # Add a leading newline if this is not the first piece of content
                            if collected_file_contents:
                                collected_file_contents.append("\n\n")
                            relative_path = os.path.relpath(file_path, item_path)
                            collected_file_contents.append(f"--- Content from (in folder {os.path.basename(item_path)}): {relative_path} ---\n")
                            collected_file_contents.append(content)
                            files_processed_count += 1
                        else:
                            files_skipped_count += 1
        
        # Combine collected file contents first
        raw_files_combined_text = "".join(collected_file_contents)
        final_text_to_copy = raw_files_combined_text # Start with file content

        # Get custom instructions
        custom_instructions = self.instructions_text_widget.get("1.0", tk.END).strip()
        
        if custom_instructions:
            if final_text_to_copy.strip(): # If there was any actual file content (not just whitespace)
                final_text_to_copy += "\n\n--- Appended Instructions ---\n"
            else: # No actual file content, or raw_files_combined_text was empty/only newlines
                final_text_to_copy = "--- Instructions ---\n" # Start fresh if no file content
            final_text_to_copy += custom_instructions
        
        # Proceed only if there's something to copy (either file content or instructions)
        if final_text_to_copy.strip():
            # Calculate stats
            char_count = len(final_text_to_copy)
            line_count = len(final_text_to_copy.splitlines())

            try:
                pyperclip.copy(final_text_to_copy)
                status_message = (
                    f"Copied to clipboard!\n"
                    f"{files_processed_count} file(s) processed, {files_skipped_count} skipped.\n"
                    f"Total lines: {line_count}, Total characters: {char_count} (including appended instructions if any)."
                )
                self.status_label.config(text=status_message)
            except pyperclip.PyperclipException as e:
                self.status_label.config(text=f"Error copying: {e}. Content length: {char_count} chars.")
                self.save_to_file(final_text_to_copy, "CollectedText_WithInstructions.txt")

        elif files_skipped_count > 0 and files_processed_count == 0 and not custom_instructions.strip():
            self.status_label.config(text=f"All {files_skipped_count} file(s) dropped were skipped. No instructions provided.")
        elif not files_processed_count and not files_skipped_count and not custom_instructions.strip():
             self.status_label.config(text="No files dropped or processed, and no instructions provided.")
        elif not final_text_to_copy.strip(): # Covers cases where only whitespace might have been generated
            self.status_label.config(text="No content (files or instructions) to copy.")


    def parse_paths(self, paths_string):
        # (parse_paths function remains the same as the previous version)
        # For brevity, I'm not repeating it here, but it should be included from the previous response.
        # It's the function that handles parsing the event.data string.
        paths_string = paths_string.strip()
        if paths_string.startswith('{') and paths_string.endswith('}'):
            paths_string = paths_string[1:-1]
        paths = []
        if '{' in paths_string and '}' in paths_string:
            import re
            matches = re.findall(r'\{([^{}]*?)\}|([^\s]+)', paths_string)
            for match_tuple in matches:
                path = match_tuple[0] if match_tuple[0] else match_tuple[1]
                if path:
                    paths.append(path.strip())
        elif ' ' in paths_string and not os.path.exists(paths_string):
            parts = paths_string.split(' ')
            current_path_candidate = ""
            for part in parts:
                if current_path_candidate: test_path = current_path_candidate + " " + part
                else: test_path = part
                if os.path.exists(test_path):
                    paths.append(test_path)
                    current_path_candidate = ""
                else:
                    if os.path.exists(part) and not current_path_candidate:
                        paths.append(part)
                        current_path_candidate = ""
                    elif current_path_candidate: current_path_candidate += " " + part
                    else: current_path_candidate = part
            if current_path_candidate and os.path.exists(current_path_candidate):
                 paths.append(current_path_candidate)
            if not paths and os.path.exists(paths_string): paths.append(paths_string)
        else:
            if os.path.exists(paths_string): paths.append(paths_string)
            else:
                potential_paths = paths_string.split('\0')
                for p_path in potential_paths:
                    if p_path.strip() and os.path.exists(p_path.strip()):
                        paths.append(p_path.strip())
        verified_paths = [p for p in paths if os.path.exists(p)]
        if not verified_paths and os.path.exists(paths_string): return [paths_string]
        return verified_paths


    def read_file_content(self, file_path):
        # (read_file_content function remains the same)
        try:
            with open(file_path, 'r', encoding='utf-8', errors='strict') as f:
                return f.read(), True
        except UnicodeDecodeError: return None, False
        except IOError: return None, False
        except Exception: return None, False

    def save_to_file(self, content, filename_suggestion="CollectedText.txt"):
        # (save_to_file function remains the same)
        try:
            from tkinter import filedialog, messagebox
            filepath = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
                title="Save collected text as...",
                initialfile=filename_suggestion
            )
            if filepath:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.status_label.config(text=f"Content saved to {os.path.basename(filepath)}")
                messagebox.showinfo("Saved", f"Content saved to {os.path.basename(filepath)}")
            else:
                self.status_label.config(text="Clipboard copy failed. Save cancelled.")
        except Exception as e:
            self.status_label.config(text=f"Failed to save file: {e}")
            messagebox.showerror("Save Error", f"Failed to save file: {e}")


if __name__ == '__main__':
    root = TkinterDnD.Tk()
    app = TextCollectorApp(root)
    root.mainloop()