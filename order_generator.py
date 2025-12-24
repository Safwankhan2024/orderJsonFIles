# order_generator.py
import os
from datetime import datetime
from pathlib import Path

def read_json_files(folder_path):
    """Get list of all JSON files in the folder."""
    return [f for f in os.listdir(folder_path) if f.endswith('.json')]

def generate_order_file(folder_path):
    """
    Generate initial order.txt file by scanning JSON files.
    Returns the path to the created order file.
    """
    json_files = read_json_files(folder_path)
    json_files.sort()  # Alphabetical sort for initial load
    
    order_file_path = os.path.join(folder_path, 'order.txt')
    with open(order_file_path, 'w') as order_file:
        for index, filename in enumerate(json_files, start=1):
            formatted_line = f"{index:03d}_{filename}"  # Changed to 03d
            order_file.write(formatted_line + '\n')
    
    return order_file_path

def parse_order_file(order_file_path):
    """
    Parse an existing order.txt file and return list of ordered filenames.
    Handles formats: "001_filename.json", "01_filename.json", or "filename.json"
    Returns tuple: (folder_path, ordered_files_list, filename_mapping)
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
            
        # STRATEGY 1: Try the full line as filename first (for timestamped files)
        original_name = line
        file_path = Path(folder_path) / original_name
        
        if file_path.exists():
            ordered_files.append(line)
            filename_mapping[line] = str(file_path)
            continue  # Success! Move to next line
            
        # STRATEGY 2: If exact match fails, try stripping numeric prefix (for order.txt files)
        parts = line.split('_', 1)
        if (len(parts) > 1 and parts[0].isdigit() and 
            (len(parts[0]) == 2 or len(parts[0]) == 3)):  # Only 2-3 digit prefixes
            original_name = parts[1]  # Everything after the first underscore
            file_path = Path(folder_path) / original_name
            
            if file_path.exists():
                ordered_files.append(line)
                filename_mapping[line] = str(file_path)
                continue  # Success after stripping prefix
                
        # STRATEGY 3: If neither works, file not found
        print(f"⚠️  File not found: {line}")
    
    return folder_path, ordered_files, filename_mapping

def save_ordered_files(folder_path, ordered_filenames):
    """
    Save ordered filenames with timestamp - PRESERVES original prefixes for readability
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    new_filename = f"ordered_{timestamp}.txt"
    new_file_path = os.path.join(folder_path, new_filename)
    
    # Keep original filenames as-is, don't strip prefixes
    with open(new_file_path, 'w') as new_file:
        for filename in ordered_filenames:
            new_file.write(filename + '\n')
    
    return new_file_path

def save_order_txt(folder_path, ordered_filenames):
    """
    Overwrite the main order.txt file (not timestamped).
    Useful for quick saves during editing.
    """
    order_file_path = os.path.join(folder_path, 'order.txt')
    
    # Strip numeric prefixes if present
    clean_filenames = []
    for filename in ordered_filenames:
        parts = filename.split('_', 1)
        if len(parts) > 1 and parts[0].isdigit():
            clean_filenames.append(parts[1])  # Remove prefix
        else:
            clean_filenames.append(filename)
    
    with open(order_file_path, 'w') as order_file:
        for index, filename in enumerate(clean_filenames, start=1):
            formatted_line = f"{index:03d}_{filename}"  # Changed to 03d
            order_file.write(formatted_line + '\n')
    
    return order_file_path