# order_generator.py
import os
from datetime import datetime
from pathlib import Path

def find_actual_file(folder_path, expected_base_name):
    """
    Find the actual file on disk that matches the base name.
    The file might have a numeric prefix or be in a subfolder.
    """
    folder = Path(folder_path)
    
    # Search for files that END WITH the expected base name
    # This handles: "01_abdominal_trauma_mcqs.json" matches "abdominal_trauma_mcqs.json"
    for f in folder.rglob("*.json"):
        if f.name.endswith(expected_base_name):
            relative_path = f.relative_to(folder_path)
            return str(f), str(relative_path)
    
    # Try case-insensitive match
    for f in folder.rglob("*.json"):
        if f.name.lower().endswith(expected_base_name.lower()):
            relative_path = f.relative_to(folder_path)
            return str(f), str(relative_path)
    
    return None, None

def parse_order_file(order_file_path):
    """
    Parse an existing order.txt file and return list of ordered filenames.
    Works with files that have numeric prefixes like "01_filename.json"
    """
    folder_path = str(Path(order_file_path).parent)
    ordered_files = []
    filename_mapping = {}
    
    with open(order_file_path, 'r') as f:
        lines = f.readlines()
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Extract base filename (remove ALL numeric prefixes)
        # "001_01_file.json" -> "file.json"
        current_name = line
        while '_' in current_name and current_name.split('_')[0].isdigit():
            parts = current_name.split('_', 1)
            if len(parts) > 1:
                current_name = parts[1]
            else:
                break
        
        # Find the actual file (searches for files ending with this name)
        actual_path, display_name = find_actual_file(folder_path, current_name)
        
        if actual_path:
            ordered_files.append(line)
            filename_mapping[line] = actual_path
        else:
            print(f"⚠️  File not found: {current_name} (from line: {line})")
    
    if not ordered_files:
        raise FileNotFoundError(f"No files found in {folder_path}. Ensure JSON files exist.")
    
    return folder_path, ordered_files, filename_mapping

def read_json_files(folder_path):
    """Get list of all JSON files in the folder."""
    return [f for f in os.listdir(folder_path) if f.endswith('.json')]

def strip_numeric_prefix(filename):
    """Remove any numeric prefix from filename."""
    parts = filename.split('_', 1)
    if len(parts) > 1 and parts[0].isdigit():
        return parts[1]
    return filename

def generate_order_file(folder_path):
    """Generate initial order.txt file by scanning JSON files."""
    json_files = read_json_files(folder_path)
    json_files.sort()
    
    order_file_path = os.path.join(folder_path, 'order.txt')
    with open(order_file_path, 'w') as order_file:
        for index, filename in enumerate(json_files, start=1):
            base_filename = strip_numeric_prefix(filename)
            formatted_line = f"{index:03d}_{base_filename}"
            order_file.write(formatted_line + '\n')
    
    return order_file_path

def save_ordered_files(folder_path, ordered_filenames):
    """Save ordered filenames with timestamp."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    new_filename = f"ordered_{timestamp}.txt"
    new_file_path = os.path.join(folder_path, new_filename)
    
    with open(new_file_path, 'w') as new_file:
        for filename in ordered_filenames:
            new_file.write(filename + '\n')
    
    return new_file_path

def save_order_txt(folder_path, ordered_filenames):
    """Overwrite the main order.txt file."""
    order_file_path = os.path.join(folder_path, 'order.txt')
    
    clean_filenames = []
    for filename in ordered_filenames:
        base_name = filename
        while '_' in base_name and base_name.split('_')[0].isdigit():
            parts = base_name.split('_', 1)
            base_name = parts[1] if len(parts) > 1 else base_name
        clean_filenames.append(base_name)
    
    with open(order_file_path, 'w') as order_file:
        for index, filename in enumerate(clean_filenames, start=1):
            formatted_line = f"{index:03d}_{filename}"
            order_file.write(formatted_line + '\n')
    
    return order_file_path