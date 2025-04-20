import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import shutil
import webbrowser
import platform
import urllib.parse

class TorrentManagerApp:
    def __init__(self, master):
        self.master = master
        master.title("Torrent Folder Manager")
        master.geometry("600x500") # Adjusted size

        self.torrents_path = None
        self.checkbox_vars = {} # {folder_name: (BooleanVar, full_path)}

        # --- Top Frame for Selection ---
        top_frame = ttk.Frame(master, padding="10")
        top_frame.pack(fill=tk.X)

        self.select_button = ttk.Button(top_frame, text="Select 'torrents' Folder", command=self.select_torrents_folder)
        self.select_button.pack(side=tk.LEFT, padx=5)

        self.path_label = ttk.Label(top_frame, text="No folder selected", wraplength=400)
        self.path_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # --- Middle Frame for Folder List (Scrollable) ---
        list_outer_frame = ttk.Frame(master, padding="10")
        list_outer_frame.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(list_outer_frame)
        self.scrollbar = ttk.Scrollbar(list_outer_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas) # Frame that holds the checkboxes

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Bind mouse wheel scrolling (platform dependent)
        if platform.system() == "Windows":
            self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        elif platform.system() == "Darwin": # macOS
             self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        else: # Linux
            self.canvas.bind_all("<Button-4>", self._on_mousewheel) # Scroll up
            self.canvas.bind_all("<Button-5>", self._on_mousewheel) # Scroll down

        # --- Bottom Frame for Info and Actions ---
        bottom_frame = ttk.Frame(master, padding="10")
        bottom_frame.pack(fill=tk.X, side=tk.BOTTOM)

        # Info Label for search links
        self.info_frame = ttk.Frame(bottom_frame)
        self.info_frame.pack(fill=tk.X, pady=(0, 10))
        self.info_label = ttk.Label(self.info_frame, text="Click on a folder name to search.", justify=tk.LEFT)
        self.info_label.pack(side=tk.LEFT, padx=5)

        # Action Buttons
        button_frame = ttk.Frame(bottom_frame)
        button_frame.pack(fill=tk.X)

        self.delete_button = ttk.Button(button_frame, text="Delete Selected", command=self.delete_selected, state=tk.DISABLED)
        self.delete_button.pack(side=tk.LEFT, padx=5)

        self.cancel_button = ttk.Button(button_frame, text="Cancel Selection", command=self.cancel_selection, state=tk.DISABLED)
        self.cancel_button.pack(side=tk.LEFT, padx=5)

        self.quit_button = ttk.Button(button_frame, text="Quit", command=self.quit_app)
        self.quit_button.pack(side=tk.RIGHT, padx=5)


    def _on_mousewheel(self, event):
        """Handle mouse wheel scrolling across different platforms."""
        if platform.system() == "Windows":
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        elif platform.system() == "Darwin": # macOS needs smaller scroll units
             self.canvas.yview_scroll(int(-1 * event.delta), "units")
        else: # Linux
            if event.num == 4: # Scroll up
                self.canvas.yview_scroll(-1, "units")
            elif event.num == 5: # Scroll down
                self.canvas.yview_scroll(1, "units")

    def select_torrents_folder(self):
        """Opens a dialog to select the 'torrents' directory."""
        # Try to find common disk roots or home directory as initial dir
        initial_dir = "/"
        if platform.system() == "Windows":
            # Check common drive letters first
            for drive in ['C:', 'D:', 'E:', 'F:']:
                 if os.path.exists(drive + '\\'):
                     initial_dir = drive + '\\'
                     break
        elif platform.system() == "Darwin":
            initial_dir = "/Volumes"
        else: # Linux
            initial_dir = os.path.expanduser("~")

        selected_path = filedialog.askdirectory(
            title="Select the 'torrents' Folder",
            initialdir=initial_dir
        )
        if selected_path:
            # Basic check if it might be the right folder name
            if os.path.basename(selected_path).lower() != "torrents":
                 # Optionally warn the user if the selected folder isn't named "torrents"
                 # messagebox.showwarning("Folder Name", "The selected folder is not named 'torrents'. Ensure it contains the correct subfolders.")
                 pass # Proceed anyway as per user selection

            self.torrents_path = selected_path
            self.path_label.config(text=f"Selected: {self.torrents_path}")
            self.populate_folder_list()
            self.clear_info_label() # Clear previous search links
            # Enable buttons only if folders are found
            if self.checkbox_vars:
                self.delete_button.config(state=tk.NORMAL)
                self.cancel_button.config(state=tk.NORMAL)
            else:
                self.delete_button.config(state=tk.DISABLED)
                self.cancel_button.config(state=tk.DISABLED)
        else:
            # User cancelled selection
            # Optionally clear the list if they cancel after having selected one before
            # self.torrents_path = None
            # self.path_label.config(text="No folder selected")
            # self.populate_folder_list() # This will clear the list
            pass


    def populate_folder_list(self):
        """Clears and refills the scrollable frame with folders from the selected path."""
        # Clear existing widgets in the scrollable frame
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.checkbox_vars.clear()

        if not self.torrents_path or not os.path.isdir(self.torrents_path):
             # Optionally show a message if the path is invalid or not selected
            # label = ttk.Label(self.scrollable_frame, text="Select a valid 'torrents' folder.")
            # label.pack(pady=10)
            self.delete_button.config(state=tk.DISABLED)
            self.cancel_button.config(state=tk.DISABLED)
            return

        try:
            found_folders = False
            entries = sorted(os.listdir(self.torrents_path), key=str.lower) # Sort alphabetically
            for entry in entries:
                full_path = os.path.join(self.torrents_path, entry)
                if os.path.isdir(full_path):
                    found_folders = True
                    var = tk.BooleanVar()
                    # Create a frame for each row (checkbox + label)
                    row_frame = ttk.Frame(self.scrollable_frame)
                    row_frame.pack(fill=tk.X, pady=1)

                    cb = ttk.Checkbutton(row_frame, variable=var, text="") # Checkbox without text initially
                    cb.pack(side=tk.LEFT, padx=(0, 5))

                    # Clickable label for the folder name to trigger search
                    label = ttk.Label(row_frame, text=entry, cursor="hand2", foreground="blue", anchor="w")
                    label.pack(side=tk.LEFT, fill=tk.X, expand=True)
                    # Use lambda to capture the current folder name for the callback
                    label.bind("<Button-1>", lambda e, name=entry: self.show_search_options(name))

                    self.checkbox_vars[entry] = (var, full_path)

            if not found_folders:
                 no_folder_label = ttk.Label(self.scrollable_frame, text="No subfolders found in the selected directory.")
                 no_folder_label.pack(pady=10)
                 self.delete_button.config(state=tk.DISABLED)
                 self.cancel_button.config(state=tk.DISABLED)
            else:
                # Only enable buttons if folders were actually listed
                self.delete_button.config(state=tk.NORMAL)
                self.cancel_button.config(state=tk.NORMAL)

        except OSError as e:
            messagebox.showerror("Error Listing Folders", f"Could not read directory:\n{self.torrents_path}\n\nError: {e}")
            self.delete_button.config(state=tk.DISABLED)
            self.cancel_button.config(state=tk.DISABLED)

        # Update canvas scroll region after adding widgets
        self.scrollable_frame.update_idletasks() # Ensure frame size is calculated
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        self.canvas.yview_moveto(0) # Scroll back to top


    def clear_info_label(self):
        """Clears the search info/link area."""
        for widget in self.info_frame.winfo_children():
            widget.destroy()
        # Re-add the default label
        self.info_label = ttk.Label(self.info_frame, text="Click on a folder name to search.", justify=tk.LEFT)
        self.info_label.pack(side=tk.LEFT, padx=5)

    def show_search_options(self, folder_name):
        """Displays links to search for the folder name on Steam and the web."""
        # Clear previous links
        for widget in self.info_frame.winfo_children():
            widget.destroy()

        search_term_encoded = urllib.parse.quote_plus(folder_name)
        steam_url = f"https://store.steampowered.com/search/?term={search_term_encoded}"
        # Use DuckDuckGo for general web search as a privacy-friendly alternative to Google
        web_search_url = f"https://duckduckgo.com/?q={search_term_encoded}"
        # Or use Google:
        # web_search_url = f"https://www.google.com/search?q={search_term_encoded}"

        prompt_label = ttk.Label(self.info_frame, text=f"Search for '{folder_name}' on:")
        prompt_label.pack(side=tk.LEFT, padx=(0, 5))

        steam_link = ttk.Label(self.info_frame, text="Steam Store", foreground="blue", cursor="hand2")
        steam_link.pack(side=tk.LEFT, padx=5)
        steam_link.bind("<Button-1>", lambda e: self.open_search_url(steam_url))

        web_link = ttk.Label(self.info_frame, text="Web Search", foreground="blue", cursor="hand2")
        web_link.pack(side=tk.LEFT, padx=5)
        web_link.bind("<Button-1>", lambda e: self.open_search_url(web_search_url))

    def open_search_url(self, url):
        """Opens the specified URL in the default web browser."""
        try:
            webbrowser.open_new_tab(url)
        except Exception as e:
            messagebox.showerror("Browser Error", f"Could not open web browser.\nURL: {url}\nError: {e}")


    def delete_selected(self):
        """Deletes folders corresponding to checked checkboxes after confirmation."""
        folders_to_delete = []
        paths_to_delete = []
        for folder_name, (var, full_path) in self.checkbox_vars.items():
            if var.get(): # If checkbox is checked
                folders_to_delete.append(folder_name)
                paths_to_delete.append(full_path)

        if not folders_to_delete:
            messagebox.showinfo("Nothing Selected", "No folders are selected for deletion.")
            return

        # Confirmation dialog
        confirm_msg = "Are you sure you want to permanently delete the following folders and all their contents?\n\n"
        confirm_msg += "\n".join([f"- {name}" for name in folders_to_delete])
        if len(confirm_msg) > 600: # Keep message somewhat short
             confirm_msg = confirm_msg[:550] + "\n\n...and possibly more."

        if messagebox.askyesno("Confirm Deletion", confirm_msg):
            deleted_count = 0
            error_count = 0
            error_messages = []

            for folder_name, path in zip(folders_to_delete, paths_to_delete):
                try:
                    print(f"Attempting to delete: {path}") # Debug print
                    shutil.rmtree(path) # This deletes the folder and everything inside
                    print(f"Successfully deleted: {path}") # Debug print
                    deleted_count += 1
                except OSError as e:
                    print(f"Error deleting {path}: {e}") # Debug print
                    error_count += 1
                    error_messages.append(f"- {folder_name}: {e}")
                except Exception as e: # Catch other potential errors
                    print(f"Unexpected error deleting {path}: {e}") # Debug print
                    error_count += 1
                    error_messages.append(f"- {folder_name}: Unexpected error - {e}")


            # Report results
            result_message = f"Deleted {deleted_count} folder(s)."
            if error_count > 0:
                result_message += f"\n\nFailed to delete {error_count} folder(s) due to errors (e.g., permissions, file in use):\n"
                result_message += "\n".join(error_messages)
                messagebox.showwarning("Deletion Partially Failed", result_message)
            else:
                messagebox.showinfo("Deletion Complete", result_message)

            # Refresh the list after deletion
            self.populate_folder_list()
            self.clear_info_label() # Clear search links after deletion

    def cancel_selection(self):
        """Deselects all checkboxes."""
        changed = False
        for var, _ in self.checkbox_vars.values():
            if var.get():
                var.set(False)
                changed = True
        #if changed:
            # Optionally provide feedback
            # messagebox.showinfo("Selection Cleared", "All selections have been cleared.")
        # No need for message box, visual feedback is enough


    def quit_app(self):
        """Closes the application."""
        self.master.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    # Use themed widgets for a more modern look if available
    style = ttk.Style()
    # Try to use a theme like 'clam', 'alt', 'default', 'classic' etc.
    # Available themes depend on the OS and Tk version.
    # ('clam' is often a good cross-platform choice)
    available_themes = style.theme_names()
    # print("Available themes:", available_themes) # Uncomment to see themes
    try:
        if 'clam' in available_themes:
            style.theme_use('clam')
        elif 'vista' in available_themes and platform.system() == "Windows":
             style.theme_use('vista') # Good theme on Windows
        elif 'aqua' in available_themes and platform.system() == "Darwin":
             style.theme_use('aqua') # Good theme on macOS
    except tk.TclError:
        print("Could not set preferred theme, using default.")


    app = TorrentManagerApp(root)
    root.mainloop()