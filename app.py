import tkinter as tk
from tkinter.constants import DISABLED, NORMAL
from tkinterdnd2 import DND_FILES, TkinterDnD
import pyperclip
import os
import tempfile
import subprocess
import sys

try:
    import pathspec
    PATHSPEC_AVAILABLE = True
    print("DEBUG: 'pathspec' library imported successfully.")
except ImportError:
    PATHSPEC_AVAILABLE = False
    print("DEBUG: 'pathspec' library not found. .gitignore processing will be disabled.")


class TextCollectorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ClipboardConcat")
        # Adjusted window size - can be tweaked further if needed
        self.root.geometry("580x500") 

        self.pathspec_warning_shown = False
        self.final_text_to_copy = ""
        self.draggable_file_path = os.path.join(tempfile.gettempdir(), "ClipboardConcat_Output.txt")

        # --- Drop Target (Now first major UI element) ---
        self.drop_target_label = tk.Label(
            self.root, text="Drag and drop text files or folders here",
            pady=20, padx=20, relief=tk.GROOVE, bd=2, font=("Arial", 12)
        )
        self.drop_target_label.pack(pady=(10,5), padx=10, expand=True, fill=tk.BOTH) # Give it some padding
        self.drop_target_label.drop_target_register(DND_FILES)
        self.drop_target_label.dnd_bind('<<Drop>>', self.on_drop)
        
        # --- Instructions Input (Now below the drop target) ---
        instructions_frame = tk.Frame(self.root)
        instructions_frame.pack(pady=5, padx=10, fill=tk.X)
        instructions_label = tk.Label(
            instructions_frame,
            text="Custom Suffix/Instructions (optional, added at the end):",
            font=("Arial", 10)
        )
        instructions_label.pack(side=tk.LEFT, anchor='w')
        self.instructions_text_widget = tk.Text(
            self.root, height=3, pady=5, padx=5, relief=tk.RIDGE, bd=1, font=("Arial", 10), wrap=tk.WORD
        ) # Reduced height slightly
        self.instructions_text_widget.pack(pady=(0, 10), padx=10, fill=tk.X)


        # --- Action Buttons Frame (Below instructions) ---
        actions_frame = tk.Frame(self.root)
        actions_frame.pack(pady=(0,10), padx=10, fill=tk.X) # Reduced bottom padding

        self.btn_copy_clipboard = tk.Button(
            actions_frame, text="Copy to Clipboard", command=self.action_copy_to_clipboard, state=DISABLED
        )
        self.btn_copy_clipboard.pack(side=tk.LEFT, expand=True, padx=5)

        self.btn_save_to_file = tk.Button(
            actions_frame, text="Save to File...", command=self.action_save_to_file, state=DISABLED
        )
        self.btn_save_to_file.pack(side=tk.LEFT, expand=True, padx=5)

        self.btn_prepare_draggable = tk.Button(
            actions_frame, text="Prepare Draggable File", command=self.action_prepare_draggable_file, state=DISABLED
        )
        self.btn_prepare_draggable.pack(side=tk.LEFT, expand=True, padx=5)


        # --- Status Label (At the bottom) ---
        self.status_label = tk.Label(self.root, text="Ready. Drop files to begin.", pady=10, font=("Arial", 9), wraplength=560, justify=tk.LEFT) # Slightly smaller font
        self.status_label.pack(fill=tk.X, padx=10, pady=(0,5))

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def on_closing(self):
        try:
            if os.path.exists(self.draggable_file_path): # Check attribute existence first
                os.remove(self.draggable_file_path)
                print(f"DEBUG: Cleaned up draggable file: {self.draggable_file_path}")
        except AttributeError: # If self.draggable_file_path was never set
            pass 
        except OSError as e:
            print(f"ERROR: Could not delete draggable file {getattr(self, 'draggable_file_path', 'N/A')} on closing: {e}")
        self.root.destroy()

    def update_action_buttons_state(self):
        new_state = NORMAL if self.final_text_to_copy and self.final_text_to_copy.strip() else DISABLED
        self.btn_copy_clipboard.config(state=new_state)
        self.btn_save_to_file.config(state=new_state)
        self.btn_prepare_draggable.config(state=new_state)

    def action_copy_to_clipboard(self):
        if not (hasattr(self, 'final_text_to_copy') and self.final_text_to_copy and self.final_text_to_copy.strip()):
            self.status_label.config(text="No content to copy.")
            return
        try:
            pyperclip.copy(self.final_text_to_copy)
            # Try to preserve existing count details if possible, or simplify
            status_summary = "Result copied to clipboard!"
            # Get details from previous status if they exist
            current_status_lines = self.status_label.cget("text").splitlines()
            detail_lines = [line for line in current_status_lines if "file(s) processed" in line or "Total lines" in line or "skipped by .gitignore" in line]
            if detail_lines:
                self.status_label.config(text=status_summary + "\n" + "\n".join(detail_lines))
            else:
                self.status_label.config(text=status_summary)

        except pyperclip.PyperclipException as e:
            self.status_label.config(text=f"Error copying to clipboard: {e}")
        except Exception as e: 
            self.status_label.config(text=f"An unexpected error occurred during copy: {e}")

    def action_save_to_file(self):
        if not (hasattr(self, 'final_text_to_copy') and self.final_text_to_copy and self.final_text_to_copy.strip()):
            self.status_label.config(text="No content to save.")
            return
        self.save_to_file(self.final_text_to_copy, "ClipboardConcat_Saved.txt")

    def action_prepare_draggable_file(self):
        if not (hasattr(self, 'final_text_to_copy') and self.final_text_to_copy and self.final_text_to_copy.strip()):
            self.status_label.config(text="No content to prepare for dragging.")
            return
        
        try:
            # Ensure the directory for the draggable file exists
            temp_dir = os.path.dirname(self.draggable_file_path)
            if not os.path.exists(temp_dir):
                os.makedirs(temp_dir, exist_ok=True)

            with open(self.draggable_file_path, "w", encoding="utf-8") as f:
                f.write(self.final_text_to_copy)
            
            if sys.platform == "win32":
                subprocess.Popen(f'explorer /select,"{os.path.normpath(self.draggable_file_path)}"')
            elif sys.platform == "darwin":
                subprocess.call(["open", "-R", os.path.normpath(self.draggable_file_path)])
            else: 
                subprocess.call(["xdg-open", os.path.normpath(os.path.dirname(self.draggable_file_path))])
            
            self.status_label.config(text=f"File ready for dragging at:\n{self.draggable_file_path}\n(File explorer opened to location)")
            print(f"INFO: Draggable file prepared at {self.draggable_file_path}")

        except Exception as e:
            self.status_label.config(text=f"Error preparing draggable file: {e}")
            print(f"ERROR: Could not prepare draggable file: {e}")

    def on_drop(self, event):
        self.status_label.config(text="Processing...")
        self.root.update_idletasks()
        
        self.final_text_to_copy = "" 
        self.update_action_buttons_state()

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
        git_ignored_count = 0

        for item_path_raw in paths:
            item_path = os.path.normpath(item_path_raw) 

            if not os.path.exists(item_path):
                # (Error message)
                continue

            if os.path.isfile(item_path):
                content, read_success = self.read_file_content(item_path)
                if read_success:
                    if collected_file_contents: collected_file_contents.append("\n\n")
                    collected_file_contents.append(f"--- Content from: {os.path.basename(item_path)} ---\n")
                    collected_file_contents.append(content)
                    files_processed_count += 1
                else:
                    files_skipped_count +=1
            elif os.path.isdir(item_path):
                gitignore_spec = None
                if PATHSPEC_AVAILABLE:
                    all_effective_patterns = []
                    for current_dir_in_walk, _, files_in_current_dir in os.walk(item_path, topdown=True):
                        if '.git' in _: _.remove('.git')
                        if '.gitignore' in files_in_current_dir:
                            gitignore_full_path = os.path.join(current_dir_in_walk, '.gitignore')
                            gitignore_dir_rel_to_item_path = os.path.relpath(current_dir_in_walk, item_path)
                            if gitignore_dir_rel_to_item_path == '.': gitignore_dir_rel_to_item_path = ''
                            try:
                                with open(gitignore_full_path, 'r', encoding='utf-8') as f_gi:
                                    for line in f_gi:
                                        pattern = line.strip()
                                        if not pattern or pattern.startswith('#'): continue
                                        is_negation = pattern.startswith('!')
                                        if is_negation: pattern = pattern[1:]
                                        
                                        # Construct effective pattern relative to item_path root
                                        # pathspec's GitWildMatchPattern handles leading '/' correctly
                                        # (relative to its .gitignore file's location).
                                        # We just need to ensure the pattern string itself is correctly scoped
                                        # if it doesn't have a leading slash, meaning it applies at that level and below.
                                        # The prefix handles scoping it to the correct subdirectory from item_path.
                                        current_pattern_for_spec = pattern
                                        if gitignore_dir_rel_to_item_path:
                                            # For a pattern like 'foo.txt' or '/foo.txt' in 'sub/.gitignore'
                                            # it becomes 'sub/foo.txt' for the master spec.
                                            # If pattern has no leading '/', pathspec treats it as '**/pattern' from its root.
                                            # If it *has* leading '/', it's from root.
                                            # Our prefixing makes the pattern absolute from item_path.
                                            
                                            # If pattern has a leading slash, it means "rooted" to its .gitignore file's dir
                                            # So, join(prefix, pattern_without_slash)
                                            # If pattern does NOT have a leading slash, it can match name anywhere in that dir or subdirs
                                            # pathspec handles `**/name` if no `/` in pattern.
                                            # `sub/name` makes it match `name` only inside `sub` or deeper if `name` is `**/*` like.

                                            # Simpler: Pathspec patterns are relative to the root of the PathSpec object.
                                            # We build ONE PathSpec rooted at item_path.
                                            # So, patterns from sub-gitignores must be prefixed.
                                            if pattern.startswith('/'):
                                                effective_pattern = os.path.join(gitignore_dir_rel_to_item_path, pattern[1:]).replace(os.sep, '/')
                                            else:
                                                effective_pattern = os.path.join(gitignore_dir_rel_to_item_path, pattern).replace(os.sep, '/')
                                        else: # .gitignore in item_path itself
                                            effective_pattern = pattern.replace(os.sep, '/') # No prefix, pattern is as-is
                                        
                                        if is_negation: effective_pattern = '!' + effective_pattern
                                        all_effective_patterns.append(effective_pattern)
                            except Exception as e: print(f"ERROR: Failed to read/process {gitignore_full_path}: {e}")
                    if all_effective_patterns:
                        try:
                            gitignore_spec = pathspec.PathSpec.from_lines(
                                pathspec.patterns.GitWildMatchPattern, all_effective_patterns
                            )
                        except Exception as e: print(f"ERROR: Could not create PathSpec for '{item_path}': {e}")
                elif not self.pathspec_warning_shown:
                    print("WARNING: 'pathspec' not installed. .gitignore files won't be processed. `pip install pathspec`")
                    self.pathspec_warning_shown = True
                
                for current_root, dirs, filenames in os.walk(item_path, topdown=True):
                    if '.git' in dirs: dirs.remove('.git')
                    for filename in filenames:
                        file_full_path = os.path.join(current_root, filename)
                        if gitignore_spec:
                            try:
                                path_to_check_vs_spec = os.path.relpath(file_full_path, item_path).replace(os.sep, '/')
                                if gitignore_spec.match_file(path_to_check_vs_spec):
                                    git_ignored_count += 1
                                    continue 
                            except: pass 
                        
                        content, read_success = self.read_file_content(file_full_path)
                        if read_success:
                            if collected_file_contents: collected_file_contents.append("\n\n")
                            relative_path = os.path.relpath(file_full_path, item_path)
                            collected_file_contents.append(f"--- Content from (folder {os.path.basename(item_path)}): {relative_path} ---\n")
                            collected_file_contents.append(content)
                            files_processed_count += 1
                        else:
                            files_skipped_count += 1
        
        raw_files_combined_text = "".join(collected_file_contents)
        current_instructions = self.instructions_text_widget.get("1.0", tk.END).strip()
        
        if raw_files_combined_text.strip() or current_instructions.strip():
            self.final_text_to_copy = raw_files_combined_text
            if current_instructions:
                if self.final_text_to_copy.strip():
                    self.final_text_to_copy += "\n\n--- Appended Instructions ---\n"
                else: 
                    self.final_text_to_copy = "--- Instructions ---\n"
                self.final_text_to_copy += current_instructions
        else:
            self.final_text_to_copy = ""

        status_lines = []
        if self.final_text_to_copy.strip():
            char_count = len(self.final_text_to_copy)
            line_count = len(self.final_text_to_copy.splitlines())
            # Corrected status message text regarding button position
            status_lines.append("Processing complete. Choose an action from the buttons above.") 
            status_lines.append(f"{files_processed_count} file(s) processed, {files_skipped_count} unreadable/binary.")
            if git_ignored_count > 0:
                status_lines.append(f"{git_ignored_count} file(s) skipped by .gitignore rules.")
            status_lines.append(f"Total lines: {line_count}, Total characters: {char_count} (incl. instructions).")
        else:
            status_lines.append("No text content processed.")
            if files_processed_count == 0 and (files_skipped_count > 0 or git_ignored_count > 0):
                 status_lines.append(f"Files: 0 read, {files_skipped_count} unreadable, {git_ignored_count} .gitignored.")

        self.status_label.config(text="\n".join(status_lines))
        self.update_action_buttons_state()

    def parse_paths(self, paths_string):
        paths_string = paths_string.strip()
        if paths_string.startswith('{') and paths_string.endswith('}'):
            paths_string = paths_string[1:-1]
        paths = []
        if '{' in paths_string and '}' in paths_string:
            import re
            matches = re.findall(r'\{([^{}]*?)\}|([^\s]+)', paths_string)
            for match_tuple in matches:
                path = match_tuple[0] if match_tuple[0] else match_tuple[1]
                if path: paths.append(path.strip())
        elif ' ' in paths_string and not os.path.exists(paths_string): # Paths with spaces, not quoted
            # This heuristic attempts to reconstruct paths that may contain spaces
            # It's not foolproof for all edge cases but handles some common scenarios
            parts = paths_string.split(' ')
            current_path_candidate = ""
            temp_paths_list = []
            for part in parts:
                if current_path_candidate:
                    test_path = current_path_candidate + " " + part
                else:
                    test_path = part
                
                # Check if the combined path exists OR if the original part was a path itself (if we are starting fresh)
                if os.path.exists(test_path):
                    temp_paths_list.append(test_path)
                    current_path_candidate = ""
                elif not current_path_candidate and os.path.exists(part): # current part is a path, and no candidate forming
                     temp_paths_list.append(part)
                     current_path_candidate = ""
                else: # Doesn't exist yet, keep building candidate
                    if current_path_candidate:
                        current_path_candidate += " " + part
                    else:
                        current_path_candidate = part
            if current_path_candidate and os.path.exists(current_path_candidate): # Add last candidate if valid
                 temp_paths_list.append(current_path_candidate)
            
            if temp_paths_list: # If heuristic found paths
                paths.extend(temp_paths_list)
            elif os.path.exists(paths_string): # Fallback: original string is a single path
                paths.append(paths_string)
        else: # Single path or paths separated by null characters (less common from explorer)
            if os.path.exists(paths_string): 
                paths.append(paths_string)
            else: # Check for null character separation
                potential_paths = paths_string.split('\0')
                for p_path in potential_paths:
                    if p_path.strip() and os.path.exists(p_path.strip()):
                        paths.append(p_path.strip())
        
        abs_paths = []
        for p in paths:
            # Ensure all paths are absolute; TkinterDnD usually provides absolute paths for DND_FILES
            # but this makes it robust.
            normalized_p = os.path.normpath(p.strip()) # Strip whitespace just in case
            if os.path.isabs(normalized_p):
                abs_paths.append(normalized_p)
            else:
                # This case is unlikely for file drops but good for robustness
                abs_paths.append(os.path.abspath(normalized_p))
        return abs_paths


    def read_file_content(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8', errors='strict') as f:
                return f.read(), True
        except UnicodeDecodeError: return None, False
        except IOError: return None, False 
        except Exception: return None, False

    def save_to_file(self, content_to_save, filename_suggestion="CollectedText.txt"):
        if not (hasattr(self, 'final_text_to_copy') and self.final_text_to_copy and self.final_text_to_copy.strip()): # Check instance var
            self.status_label.config(text="No content to save.")
            from tkinter import messagebox 
            messagebox.showwarning("No Content", "There is no content to save.")
            return

        try:
            from tkinter import filedialog, messagebox 
            filepath = filedialog.asksaveasfilename(
                defaultextension=".txt", filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
                title="Save collected text as...", initialfile=filename_suggestion
            )
            if filepath:
                with open(filepath, 'w', encoding='utf-8') as f: f.write(content_to_save) # Use passed content_to_save
                status_summary = f"Result saved to {os.path.basename(filepath)}"
                current_status_lines = self.status_label.cget("text").splitlines()
                detail_lines = [line for line in current_status_lines if "file(s) processed" in line or "Total lines" in line or "skipped by .gitignore" in line]
                if detail_lines:
                    self.status_label.config(text=status_summary + "\n" + "\n".join(detail_lines))
                else:
                    self.status_label.config(text=status_summary)
                messagebox.showinfo("Saved", f"Content saved to {os.path.basename(filepath)}")
            else: 
                 current_status_lines = self.status_label.cget("text").splitlines()
                 # Preserve first line of status (usually "Processing complete...")
                 first_line = current_status_lines[0] if current_status_lines else "Status:"
                 self.status_label.config(text=first_line + "\nSave operation cancelled.")
        except Exception as e:
            self.status_label.config(text=f"Failed to save file: {e}")
            if 'messagebox' not in locals(): from tkinter import messagebox
            messagebox.showerror("Save Error", f"Failed to save file: {e}")

if __name__ == '__main__':
    root = TkinterDnD.Tk() 
    app = TextCollectorApp(root)
    root.mainloop()