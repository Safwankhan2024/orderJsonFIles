import tkinter as tk
from tkinter import filedialog, messagebox
from order_generator import generate_order_file, save_ordered_files

class OrderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("JSON File Orderer")

        # Create UI elements
        self.create_widgets()

        # Variables to store folder path and ordered files
        self.folder_path = ""
        self.ordered_files = []

    def create_widgets(self):
        # Folder selection button
        self.select_folder_btn = tk.Button(self.root, text="Select Folder", command=self.select_folder)
        self.select_folder_btn.pack(pady=10)

        # Listbox to display files
        self.file_listbox = tk.Listbox(self.root, selectmode=tk.SINGLE, height=20, width=60)
        self.file_listbox.pack(pady=10)

        # Buttons for file operations
        self.up_btn = tk.Button(self.root, text="Move Up", command=self.move_up)
        self.up_btn.pack(side=tk.LEFT, padx=5)

        self.down_btn = tk.Button(self.root, text="Move Down", command=self.move_down)
        self.down_btn.pack(side=tk.LEFT, padx=5)

        # Generate order button
        self.generate_order_btn = tk.Button(self.root, text="Generate Order File", command=self.generate_order_file)
        self.generate_order_btn.pack(pady=10)

    def select_folder(self):
        self.folder_path = filedialog.askdirectory()
        if self.folder_path:
            # Generate initial order file and populate listbox
            order_file_path = generate_order_file(self.folder_path)
            with open(order_file_path, 'r') as f:
                self.ordered_files = [line.strip() for line in f.readlines()]
            self.update_listbox()

    def update_listbox(self):
        self.file_listbox.delete(0, tk.END)
        for filename in self.ordered_files:
            self.file_listbox.insert(tk.END, filename)

    def move_up(self):
        selected_index = self.file_listbox.curselection()
        if not selected_index:
            return
        index = selected_index[0]
        if index > 0:
            # Swap with previous item
            self.ordered_files[index], self.ordered_files[index-1] = self.ordered_files[index-1], self.ordered_files[index]
            self.update_listbox()
            self.file_listbox.selection_set(index-1)

    def move_down(self):
        selected_index = self.file_listbox.curselection()
        if not selected_index:
            return
        index = selected_index[0]
        if index < len(self.ordered_files) - 1:
            # Swap with next item
            self.ordered_files[index], self.ordered_files[index+1] = self.ordered_files[index+1], self.ordered_files[index]
            self.update_listbox()
            self.file_listbox.selection_set(index+1)

    def generate_order_file(self):
        if not self.folder_path:
            messagebox.showwarning("Warning", "Please select a folder first")
            return

        # Save the ordered files with timestamp
        new_file_path = save_ordered_files(self.folder_path, self.ordered_files)
        messagebox.showinfo("Success", f"New order file created: {new_file_path}")

if __name__ == "__main__":
    root = tk.Tk()
    app = OrderApp(root)
    root.mainloop()
