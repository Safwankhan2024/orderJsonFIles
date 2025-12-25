# order_generator.py
import os
from datetime import datetime
from pathlib import Path

def find_all_json_files(folder_path):
    """
    Find all JSON files in the folder and mcq_json subfolder.
    Returns list of (relative_path, display_name) tuples with ORIGINAL names.
    """
    folder = Path(folder_path)
    files = []
    
    # Search in mcq_json subfolder (most common)
    mcq_folder = folder / "mcq_json"
    if mcq_folder.exists():
        for f in sorted(mcq_folder.glob("*.json")):
            if f.name not in ["order.txt"] and not f.name.startswith("ordered_"):
                relative_path = f.relative_to(folder)
                files.append((str(relative_path), f.name))
    
    # If no files in mcq_json, try main folder
    if not files:
        for f in sorted(folder.glob("*.json")):
            if f.name not in ["order.txt"] and not f.name.startswith("ordered_"):
                files.append((f.name, f.name))
    
    return files

def parse_order_file(order_file_path):
    """
    Parse an existing order.txt file.
    Each line is treated as an EXACT filename to find (e.g., "01_abdominal_trauma_mcqs.json").
    """
    folder_path = str(Path(order_file_path).parent)
    ordered_files = []
    filename_mapping = {}
    
    with open(order_file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # The line IS the filename - find it exactly as written
        folder = Path(folder_path)
        
        # Try mcq_json subfolder first
        mcq_path = folder / "mcq_json" / line
        if mcq_path.exists():
            ordered_files.append(line)
            filename_mapping[line] = str(mcq_path)
            continue
        
        # Try main folder
        main_path = folder / line
        if main_path.exists():
            ordered_files.append(line)
            filename_mapping[line] = str(main_path)
            continue
        
        # Try case-insensitive search as last resort
        found = False
        for f in folder.rglob("*.json"):
            if f.name.lower() == line.lower():
                relative_path = f.relative_to(folder_path)
                ordered_files.append(line)
                filename_mapping[line] = str(f)
                found = True
                break
        
        if not found:
            print(f"⚠️  File not found: {line}")
    
    if not ordered_files:
        raise FileNotFoundError(f"No files found in {folder_path}. Ensure JSON files exist.")
    
    return folder_path, ordered_files, filename_mapping

def generate_initial_order_file(folder_path):
    """
    Generate initial order.txt from scratch.
    Uses ORIGINAL filenames exactly as they are on disk.
    """
    files = find_all_json_files(folder_path)
    if not files:
        raise FileNotFoundError(f"No JSON files found in {folder_path}")
    
    order_file_path = os.path.join(folder_path, 'order.txt')
    with open(order_file_path, 'w', encoding='utf-8') as f:
        for relative_path, display_name in files:
            # Store the relative path (e.g., "mcq_json/01_file.json")
            f.write(f"{relative_path}\n")
    
    return order_file_path

def save_ordered_files(folder_path, ordered_filenames):
    """
    Save ordered filenames with timestamp - preserves EXACT names
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    new_filename = f"ordered_{timestamp}.txt"
    new_file_path = os.path.join(folder_path, new_filename)
    
    with open(new_file_path, 'w', encoding='utf-8') as f:
        for filename in ordered_filenames:
            f.write(filename + '\n')
    
    return new_file_path

def save_order_txt(folder_path, ordered_filenames):
    """
    Overwrite the main order.txt file - preserves EXACT names
    """
    order_file_path = os.path.join(folder_path, 'order.txt')
    
    with open(order_file_path, 'w', encoding='utf-8') as f:
        for filename in ordered_filenames:
            f.write(filename + '\n')
    
    return order_file_path