import tkinter as tk
from tkinter import filedialog, messagebox
from order_generator import generate_order_file, save_ordered_files

class OrderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("JSON File Orderer")

        # Set window size to better utilize 1080p resolution
        self.root.geometry("1000x700")  # Width x Height

        # Create UI elements
        self.create_widgets()

        # Variables to store folder path and ordered files
        self.folder_path = ""
        self.ordered_files = []

        # Drag-and-drop variables
        self.drag_index = None

    def create_widgets(self):
        # Folder selection button
        self.select_folder_btn = tk.Button(self.root, text="Select Folder", command=self.select_folder)
        self.select_folder_btn.pack(pady=10)

        # Frame for listbox and scrollbar
        control_frame = tk.Frame(self.root)
        control_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Listbox to display files with drag-and-drop support
        self.file_listbox = tk.Listbox(control_frame, selectmode=tk.SINGLE, height=30, width=100)
        self.file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        # Add vertical scrollbar
        self.scrollbar = tk.Scrollbar(control_frame, orient=tk.VERTICAL, command=self.file_listbox.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.file_listbox.config(yscrollcommand=self.scrollbar.set)

        # Bind mouse events for drag-and-drop
        self.file_listbox.bind('<Button-1>', self.on_listbox_click)
        self.file_listbox.bind('<B1-Motion>', self.on_listbox_drag)
        self.file_listbox.bind('<ButtonRelease-1>', self.on_listbox_release)

        # Buttons frame
        button_frame = tk.Frame(control_frame)
        button_frame.pack(side=tk.LEFT, fill=tk.Y)

        # Reorder buttons
        self.up_btn = tk.Button(button_frame, text="Move Up", command=self.move_up)
        self.up_btn.pack(pady=5, padx=5, fill=tk.X)

        self.down_btn = tk.Button(button_frame, text="Move Down", command=self.move_down)
        self.down_btn.pack(pady=5, padx=5, fill=tk.X)

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

    def on_listbox_click(self, event):
        """Start drag operation"""
        self.drag_index = self.file_listbox.nearest(event.y)
        self.file_listbox.selection_set(self.drag_index)

    def on_listbox_drag(self, event):
        """Move item during drag"""
        if self.drag_index is not None:
            over_index = self.file_listbox.nearest(event.y)

            # If dragging up
            if over_index < self.drag_index:
                selected_item = self.ordered_files.pop(self.drag_index)
                self.ordered_files.insert(over_index, selected_item)
                self.update_listbox()
                self.file_listbox.selection_set(over_index)
                self.drag_index = over_index

            # If dragging down
            elif over_index > self.drag_index:
                selected_item = self.ordered_files.pop(self.drag_index)
                self.ordered_files.insert(over_index - 1, selected_item)
                self.update_listbox()
                self.file_listbox.selection_set(over_index - 1)
                self.drag_index = over_index - 1

    def on_listbox_release(self, event):
        """End drag operation"""
        self.drag_index = None

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
