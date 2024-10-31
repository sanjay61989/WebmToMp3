import os
import subprocess
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
from concurrent.futures import ThreadPoolExecutor, as_completed


# Define the GUI application class
class ConverterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("WebM to MP3 Converter")
        self.root.geometry("1000x600")  # Increase the size of the main window

        # Paths for webm and mp3 files
        self.webm_path = ""
        self.mp3_path = ""
        self.total_files = 0
        self.completed_files = 0

        # Setup GUI elements
        self.setup_gui()

    def setup_gui(self):
        # Label and button for selecting the webm directory
        tk.Label(self.root, text="Select WebM Directory").grid(row=0, column=0, pady=10)
        tk.Button(self.root, text="Browse", command=self.select_webm_dir).grid(
            row=0, column=1
        )
        self.webm_path_label = tk.Label(
            self.root, text="", wraplength=300
        )  # Label to show selected path
        self.webm_path_label.grid(row=0, column=2)

        # Label and button for selecting the mp3 directory
        tk.Label(self.root, text="Select MP3 Directory").grid(row=1, column=0, pady=10)
        tk.Button(self.root, text="Browse", command=self.select_mp3_dir).grid(
            row=1, column=1
        )
        self.mp3_path_label = tk.Label(
            self.root, text="", wraplength=300
        )  # Label to show selected path
        self.mp3_path_label.grid(row=1, column=2)

        # Total files label
        self.total_files_label = tk.Label(
            self.root, text="Total Files: 0, Remaining: 0"
        )
        self.total_files_label.grid(row=2, column=0, columnspan=3, pady=10)

        # Progress bar
        self.progress = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            self.root, variable=self.progress, maximum=100
        )
        self.progress_bar.grid(row=3, column=0, columnspan=3, pady=20, sticky="we")
        self.percentage_label = tk.Label(self.root, text="0%", font=("Arial", 14))
        self.percentage_label.grid(row=3, column=4, columnspan=1, pady=20, sticky="we")
        # Active conversions listbox
        tk.Label(self.root, text="Active Conversions").grid(row=4, column=0)
        self.active_listbox = tk.Listbox(self.root, width=50, height=15)
        self.active_listbox.grid(row=5, column=0, padx=10, pady=5)

        # Completed conversions listbox
        tk.Label(self.root, text="Completed Conversions").grid(row=4, column=1)
        self.completed_listbox = tk.Listbox(self.root, width=50, height=15)
        self.completed_listbox.grid(row=5, column=1, padx=10, pady=5)

        # Convert button
        self.convert_button = tk.Button(
            self.root, text="Convert", command=self.start_conversion, state="disabled"
        )
        self.convert_button.grid(row=6, column=0, columnspan=2, pady=10)

    def select_webm_dir(self):
        self.webm_path = filedialog.askdirectory()
        if self.webm_path:
            self.webm_path_label.config(text=self.webm_path)
            self.update_total_files_count()
            self.update_convert_button_state()

    def select_mp3_dir(self):
        self.mp3_path = filedialog.askdirectory()
        if not self.mp3_path:
            # Default to webm_path if mp3_path is not selected
            self.mp3_path = self.webm_path
        self.mp3_path_label.config(text=self.mp3_path)
        self.update_convert_button_state()

    def update_convert_button_state(self):
        if self.webm_path:
            self.convert_button.config(state="normal")

    def update_total_files_count(self):
        webm_files = [f for f in os.listdir(self.webm_path) if f.endswith(".webm")]
        self.total_files = len(webm_files)
        self.completed_files = 0  # Reset completed files count
        self.total_files_label.config(
            text=f"Total Files: {self.total_files}, Remaining: {self.total_files}"
        )

    def start_conversion(self):
        # Disable the button during conversion
        self.convert_button.config(state="disabled")
        self.active_listbox.delete(0, tk.END)  # Clear the active conversions list
        self.completed_listbox.delete(0, tk.END)  # Clear the completed conversions list

        # Run the conversion in a separate thread
        threading.Thread(target=self.convert_files).start()

    def convert_files(self):
        # Collect WebM files
        webm_files = [f for f in os.listdir(self.webm_path) if f.endswith(".webm")]

        if not webm_files:
            messagebox.showinfo(
                "No Files", "No WebM files found in the selected directory."
            )
            self.convert_button.config(state="normal")
            return

        # Process files in batches of 5
        for i in range(0, len(webm_files), 5):
            # Select a batch of up to 5 files
            batch = webm_files[i : i + 5]
            futures = []

            # Set up concurrent conversion
            with ThreadPoolExecutor(max_workers=5) as executor:
                for file in batch:
                    webm_file_path = os.path.join(self.webm_path, file)
                    mp3_file_path = os.path.join(self.mp3_path, file).replace(
                        ".webm", ".mp3"
                    )

                    # Create a future for each conversion task
                    future = executor.submit(
                        self.convert_file, webm_file_path, mp3_file_path, file
                    )
                    futures.append(future)

                    # Add active conversion to the list
                    self.active_listbox.insert(tk.END, f"{file}")

                # Track progress
                for future in as_completed(futures):
                    try:
                        self.completed_files += 1

                        # Update the active conversions list
                        self.active_listbox.delete(0, tk.END)  # Clear the active list
                        for f in futures:
                            if not f.done():
                                # If the file conversion is not done, add it back to the list
                                self.active_listbox.insert(tk.END, f"{future.result()}")

                        # Update total progress bar
                        self.progress.set(
                            (self.completed_files / self.total_files) * 100
                        )
                        self.percentage_label.config(
                            text=f"{int(self.progress.get())}%"
                        )

                        # Update remaining file count
                        remaining_files = self.total_files - self.completed_files
                        self.total_files_label.config(
                            text=f"Total Files: {self.total_files}, Remaining: {remaining_files}"
                        )

                        # Get the name of the completed file
                        file_name = future.result()
                        self.completed_listbox.insert(tk.END, file_name)

                    except Exception as e:
                        # Show error message in a popup
                        messagebox.showerror(
                            "Conversion Error", f"Error converting file: {e}"
                        )
                        self.active_listbox.delete(0, tk.END)  # Clear the active list

                    self.root.update_idletasks()

        messagebox.showinfo("Conversion Complete", "All files have been processed!")
        self.convert_button.config(state="normal")

    def convert_file(self, webm_file, mp3_file, file_name):
        command = f'ffmpeg -i "{webm_file}" -vn -ab 320k -ar 44100 -y "{mp3_file}"'
        subprocess.call(command, shell=True)

        # Return the name for status updates
        return file_name


# Run the application
if __name__ == "__main__":
    root = tk.Tk()
    app = ConverterApp(root)
    root.mainloop()
