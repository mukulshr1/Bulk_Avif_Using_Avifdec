import os
import subprocess
from tkinter import Tk, Label, Button, filedialog, messagebox, StringVar
from PIL import Image
import concurrent.futures
import threading
import multiprocessing

# Supported image formats
SUPPORTED_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp')

# Path to avifenc.exe (change this if it's located elsewhere)
AVIFENC_PATH = os.path.abspath("avifenc.exe")

class ImageConverterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AVIF Converter with Folder Structure")
        self.root.geometry("420x330")

        self.input_folder = ""
        self.output_folder = ""

        # Thread-safe counters
        self.total = 0
        self.completed = 0
        self.lock = threading.Lock()

        # Status display
        self.total_files_var = StringVar(value="Total Files: 0")
        self.remaining_files_var = StringVar(value="Remaining Files: 0")
        self.completed_files_var = StringVar(value="Completed Files: 0")

        # UI Components
        Label(root, text="Select input folder:").pack(pady=5)
        Button(root, text="Browse Input Folder", command=self.browse_input_folder).pack()

        Label(root, text="Select output folder:").pack(pady=5)
        Button(root, text="Browse Output Folder", command=self.browse_output_folder).pack()

        Button(root, text="Convert to AVIF", command=self.start_conversion_thread, bg='green', fg='white').pack(pady=10)

        Label(root, textvariable=self.total_files_var).pack()
        Label(root, textvariable=self.remaining_files_var).pack()
        Label(root, textvariable=self.completed_files_var).pack()

    def browse_input_folder(self):
        self.input_folder = filedialog.askdirectory(title="Select Input Folder")

    def browse_output_folder(self):
        self.output_folder = filedialog.askdirectory(title="Select Output Folder")

    def start_conversion_thread(self):
        thread = threading.Thread(target=self.start_conversion)
        thread.start()

    def update_status(self):
        remaining = self.total - self.completed
        self.completed_files_var.set(f"Completed Files: {self.completed}")
        self.remaining_files_var.set(f"Remaining Files: {remaining}")
        self.root.update_idletasks()

    def convert_single_file(self, full_input_path, relative_path):
        # Destination path preserving folder structure
        output_path = os.path.join(self.output_folder, os.path.splitext(relative_path)[0] + ".avif")
        output_dir = os.path.dirname(output_path)
        os.makedirs(output_dir, exist_ok=True)

        try:
            subprocess.run([AVIFENC_PATH, full_input_path, output_path], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error converting {relative_path}: {e}")
        finally:
            with self.lock:
                self.completed += 1
                self.update_status()

    def gather_image_files(self):
        image_files = []
        for root_dir, _, files in os.walk(self.input_folder):
            for file in files:
                if file.lower().endswith(SUPPORTED_EXTENSIONS):
                    full_path = os.path.join(root_dir, file)
                    rel_path = os.path.relpath(full_path, self.input_folder)
                    image_files.append((full_path, rel_path))
        return image_files

    def start_conversion(self):
        if not self.input_folder or not self.output_folder:
            messagebox.showwarning("Missing Paths", "Please select both input and output folders.")
            return

        if not os.path.exists(AVIFENC_PATH):
            messagebox.showerror("Error", f"avifenc.exe not found at {AVIFENC_PATH}")
            return

        image_files = self.gather_image_files()
        self.total = len(image_files)
        self.completed = 0

        if self.total == 0:
            messagebox.showinfo("No Files", "No supported image files found.")
            return

        self.total_files_var.set(f"Total Files: {self.total}")
        self.remaining_files_var.set(f"Remaining Files: {self.total}")
        self.completed_files_var.set(f"Completed Files: 0")

        max_workers = multiprocessing.cpu_count()
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            for full_path, rel_path in image_files:
                executor.submit(self.convert_single_file, full_path, rel_path)

        messagebox.showinfo("Done", f"Conversion completed. {self.completed} files converted.")

if __name__ == "__main__":
    root = Tk()
    app = ImageConverterApp(root)
    root.mainloop()
