# order_gui.py - Dark Theme Edition for Eye Comfort
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
from order_generator import (
    generate_order_file, 
    save_ordered_files, 
    parse_order_file,
    save_order_txt
)

class OrderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("JSON File Orderer - Dark Mode")
        self.root.geometry("1200x800")
        
        # Dark theme color palette - adjusted for better readability
        self.colors = {
            'bg': '#1e1e1e',           # Main background
            'fg': '#e0e0e0',           # Main text
            'listbox_bg': '#2b2b2b',   # Listbox background
            'listbox_fg': '#e0e0e0',   # Listbox text
            'select_bg': '#4a4a4a',    # Selection color (less harsh)
            'select_fg': '#ffffff',     # Selection text
            'button_bg': '#3c3f41',    # Button background
            'button_fg': '#ffffff',     # Button text
            'button_active': '#4a4c4d',
            'disabled_bg': '#2d2d2d',
            'disabled_fg': '#999999',
            'success': '#6ccf6c',      # Green for success messages
            'warning': '#ffcc66'       # Yellow for warnings
        }
        
        # Configure root window
        self.root.configure(bg=self.colors['bg'])
        
        # Configure global text for better readability
        self.default_font = ('Segoe UI', 10)  # Clear, modern font
        self.root.option_add('*Font', self.default_font)
        self.root.option_add('*Background', self.colors['bg'])
        self.root.option_add('*Foreground', self.colors['fg'])
        
        # Configure listbox default colors
        self.root.option_add('*Listbox*Background', self.colors['listbox_bg'])
        self.root.option_add('*Listbox*Foreground', self.colors['listbox_fg'])
        self.root.option_add('*Listbox*selectBackground', self.colors['select_bg'])
        self.root.option_add('*Listbox*selectForeground', self.colors['select_fg'])

        self.folder_path = ""
        self.ordered_files = []
        self.drag_index = None
        self.filename_mapping = {}

        self.create_widgets()

    def create_widgets(self):
        # Top button frame
        top_button_frame = tk.Frame(self.root, bg=self.colors['bg'])
        top_button_frame.pack(pady=15)

        # Configure button style
        button_style = {
            'bg': self.colors['button_bg'],
            'fg': self.colors['button_fg'],
            'activebackground': self.colors['button_active'],
            'activeforeground': self.colors['button_fg'],
            'relief': 'flat',
            'padx': 12,
            'pady': 6,
            'cursor': 'hand2',
            'font': ('Segoe UI', 10, 'bold')
        }

        self.select_folder_btn = tk.Button(
            top_button_frame, 
            text="📁 Select Folder", 
            command=self.select_folder,
            **button_style
        )
        self.select_folder_btn.pack(side=tk.LEFT, padx=8)

        self.load_order_btn = tk.Button(
            top_button_frame, 
            text="📄 Load Order File", 
            command=self.load_order_file,
            **button_style
        )
        self.load_order_btn.pack(side=tk.LEFT, padx=8)

        # Listbox frame
        control_frame = tk.Frame(self.root, bg=self.colors['bg'])
        control_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Configure listbox with dark theme
        listbox_style = {
            'selectmode': tk.SINGLE,
            'height': 35,
            'width': 120,
            'bg': self.colors['listbox_bg'],
            'fg': self.colors['listbox_fg'],
            'selectbackground': self.colors['select_bg'],
            'selectforeground': self.colors['select_fg'],
            'relief': 'flat',
            'highlightthickness': 0,
            'font': ('Consolas', 10)  # Monospaced font for filenames
        }

        self.file_listbox = tk.Listbox(control_frame, **listbox_style)
        self.file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        # Configure scrollbar for dark theme
        self.scrollbar = tk.Scrollbar(
            control_frame, 
            orient=tk.VERTICAL, 
            command=self.file_listbox.yview,
            bg=self.colors['button_bg'],
            troughcolor=self.colors['listbox_bg'],
            activebackground=self.colors['button_active']
        )
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.file_listbox.config(yscrollcommand=self.scrollbar.set)

        # Bind drag-and-drop events
        self.file_listbox.bind('<Button-1>', self.on_listbox_click)
        self.file_listbox.bind('<B1-Motion>', self.on_listbox_drag)
        self.file_listbox.bind('<ButtonRelease-1>', self.on_listbox_release)

        # Reorder buttons frame
        button_frame = tk.Frame(control_frame, bg=self.colors['bg'])
        button_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5)

        # Configure reorder buttons
        reorder_button_style = {
            **button_style,
            'width': 12,
            'font': ('Segoe UI', 9, 'bold')
        }
        
        self.up_btn = tk.Button(
            button_frame, 
            text="⬆ Move Up", 
            command=self.move_up,
            **reorder_button_style
        )
        self.up_btn.pack(pady=6, fill=tk.X)

        self.down_btn = tk.Button(
            button_frame, 
            text="⬇ Move Down", 
            command=self.move_down,
            **reorder_button_style
        )
        self.down_btn.pack(pady=6, fill=tk.X)

        # Generate order button (green accent for primary action)
        self.generate_order_btn = tk.Button(
            self.root, 
            text="✓ Generate Order File", 
            command=self.generate_order_file,
            bg='#2d5d2d',  # Dark green
            fg='#ffffff',
            activebackground='#3d6d3d',
            activeforeground='#ffffff',
            relief='flat',
            padx=20,
            pady=10,
            cursor='hand2',
            font=('Segoe UI', 11, 'bold')
        )
        self.generate_order_btn.pack(pady=15)

    def select_folder(self):
        """Select a folder and generate initial order from JSON files."""
        self.folder_path = filedialog.askdirectory()
        if self.folder_path:
            try:
                order_file_path = generate_order_file(self.folder_path)
                self.folder_path, self.ordered_files, self.filename_mapping = parse_order_file(order_file_path)
                self.update_listbox()
                messagebox.showinfo(
                    "✓ Success", 
                    f"Loaded folder and generated initial order from {len(self.ordered_files)} files"
                )
            except Exception as e:
                messagebox.showerror("✗ Error", f"Failed to load files: {e}")

    def load_order_file(self):
        """Load an existing order.txt file to resume previous sorting work."""
        order_file_path = filedialog.askopenfilename(
            title="Select Order File",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if order_file_path:
            try:
                self.folder_path, self.ordered_files, self.filename_mapping = parse_order_file(order_file_path)
                self.update_listbox()
                messagebox.showinfo(
                    "✓ Success", 
                    f"Loaded order file with {len(self.ordered_files)} files. Ready to resume sorting!"
                )
            except Exception as e:
                messagebox.showerror("✗ Error", f"Failed to load order file: {e}")

    def update_listbox(self):
        """Updates the listbox while preserving scroll position."""
        current_yview = self.file_listbox.yview()
        self.file_listbox.delete(0, tk.END)
        
        for filename in self.ordered_files:
            self.file_listbox.insert(tk.END, filename)
            
        if self.drag_index is not None and self.drag_index < len(self.ordered_files):
            self.file_listbox.selection_set(self.drag_index)
            
        self.file_listbox.yview_moveto(current_yview[0])

    def on_listbox_click(self, event):
        """Start drag operation."""
        self.drag_index = self.file_listbox.nearest(event.y)
        if self.drag_index >= len(self.ordered_files):
            self.drag_index = None
            return
            
        self.file_listbox.selection_clear(0, tk.END)
        self.file_listbox.selection_set(self.drag_index)

    def on_listbox_drag(self, event):
        """Move item during drag."""
        if self.drag_index is None:
            return

        # Auto-scrolling with adjusted speed
        height = self.file_listbox.winfo_height()
        if event.y < 30:
            self.scroll_up()
        elif event.y > height - 30:
            self.scroll_down()

        new_index = self.file_listbox.nearest(event.y)
        if new_index != self.drag_index and 0 <= new_index < len(self.ordered_files):
            item = self.ordered_files.pop(self.drag_index)
            self.ordered_files.insert(new_index, item)
            self.drag_index = new_index
            self.update_listbox()

    def on_listbox_release(self, event):
        """End drag operation."""
        self.drag_index = None

    def scroll_up(self):
        self.file_listbox.yview_scroll(-1, "units")

    def scroll_down(self):
            self.file_listbox.yview_scroll(1, "units")

    def move_up(self):
        selected_index = self.file_listbox.curselection()
        if not selected_index:
            return
        index = selected_index[0]
        if index > 0:
            self.ordered_files[index], self.ordered_files[index-1] = self.ordered_files[index-1], self.ordered_files[index]
            self.update_listbox()
            self.file_listbox.selection_set(index-1)

    def move_down(self):
        selected_index = self.file_listbox.curselection()
        if not selected_index:
            return
        index = selected_index[0]
        if index < len(self.ordered_files) - 1:
            self.ordered_files[index], self.ordered_files[index+1] = self.ordered_files[index+1], self.ordered_files[index]
            self.update_listbox()
            self.file_listbox.selection_set(index+1)

    def generate_order_file(self):
        #    """Generate final order file - creates both timestamped backup and main order.txt."""
        if not self.folder_path:
            messagebox.showwarning("⚠ Warning", "Please select a folder first or load an order file")
            return

        try:
            # Create timestamped backup
            new_file_path = save_ordered_files(self.folder_path, self.ordered_files)
                
                # Also update main order.txt
            order_txt_path = save_order_txt(self.folder_path, self.ordered_files)
                
            messagebox.showinfo(
                    "✓ Success", 
                    f"Order files created:\n\n"
                    f"Main: {order_txt_path}\n"
                    f"Backup: {new_file_path}"
                )
        except Exception as e:
            messagebox.showerror("✗ Error", f"Failed to save file: {e}")

if __name__ == "__main__":
        root = tk.Tk()
        app = OrderApp(root)
        root.mainloop()