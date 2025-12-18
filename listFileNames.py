import os
import json

# Get the directory where the script is located
current_dir = os.path.dirname(os.path.abspath(__file__))

# Display options to the user
print("Options:")
print("1: List file names in the current folder only (skip subfolders)")
print("2: Skip current folder and list file names from immediate subfolders only (with subfolder prefix)")
print("3: Skip current folder and list file names from all subfolders recursively (with full relative path hierarchy)")

# Get user choice
choice = input("\nEnter your choice (1, 2, or 3): ").strip()

files = []

if choice == '1':
    # Option 1: Files in current directory only
    for item in os.listdir(current_dir):
        full_path = os.path.join(current_dir, item)
        if os.path.isfile(full_path):
            files.append(item)

elif choice == '2':
    # Option 2: Files in immediate subfolders only (skip current folder)
    for subdir in os.listdir(current_dir):
        sub_path = os.path.join(current_dir, subdir)
        if os.path.isdir(sub_path):
            for item in os.listdir(sub_path):
                item_path = os.path.join(sub_path, item)
                if os.path.isfile(item_path):
                    # Use relative path: subfolder/filename
                    rel_path = os.path.join(subdir, item)
                    files.append(rel_path)

elif choice == '3':
    # Option 3: All files in subfolders recursively (skip current folder), preserve hierarchy
    for root, dirs, filenames in os.walk(current_dir):
        if root == current_dir:
            continue  # Skip the current directory itself
        for filename in filenames:
            full_path = os.path.join(root, filename)
            # Relative path from the script's directory
            rel_path = os.path.relpath(full_path, current_dir)
            files.append(rel_path)

else:
    print("Invalid choice. Please run again and select 1, 2, or 3.")
    exit()

# Normalize all paths to use '/' for consistency across platforms
files = [f.replace('\\', '/') for f in files]

# Prepare the output data
output_data = {
    "directory_scanned": current_dir,
    "option_chosen": choice,
    "description": {
        "1": "Current folder only",
        "2": "Immediate subfolders only",
        "3": "All subfolders recursively (with hierarchy)"
    }.get(choice, "unknown"),
    "files": files
}

# Save to JSON file in the same directory
output_file = os.path.join(current_dir, "file_list_output.json")

with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(output_data, f, indent=4)

print(f"\nSuccessfully saved {len(files)} file name(s) to:")
print(f"   {output_file}")

# Now, offer the filtering option
# --- IMPROVED FILTERING LOGIC ---
filter_choice = input("\nFilter out folders containing files starting with a specific pattern? (y/n): ").strip().lower()

if filter_choice == 'y':
    pattern = input("Enter the pattern (e.g., done_): ").strip()
    
    # 1. First Pass: Identify all directories that contain a 'done' file
    bad_dirs = set()
    for f in files:
        basename = os.path.basename(f)
        dirname = os.path.dirname(f)
        if basename.startswith(pattern):
            # We mark this directory as "processed"
            bad_dirs.add(dirname)
    
    # 2. Second Pass: Filter the list to exclude any file inside those directories
    filtered_files = []
    for f in files:
        file_dir = os.path.dirname(f)
        
        # Check if this file's directory (or any parent directory) is in the bad_dirs list
        is_in_bad_dir = False
        for bd in bad_dirs:
            # If bd is empty, it means a 'done_' file was found in the root
            if bd == "":
                if file_dir == "":
                    is_in_bad_dir = True
                    break
            # Use os.sep to ensure "folder\file" matches "folder" + "\"
            elif f.startswith(bd + os.sep) or f == bd:
                is_in_bad_dir = True
                break
        
        if not is_in_bad_dir:
            filtered_files.append(f)
    
    # Update output_data for the new JSON file
    output_data['files'] = filtered_files
    output_data['filtered'] = True
    output_data['filter_pattern'] = pattern
    
    # Save to a new filtered JSON file
    filtered_output_file = os.path.join(current_dir, "filtered_file_list_output.json")
    with open(filtered_output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=4)
    
    print(f"\nSuccessfully excluded folders containing '{pattern}' files.")
    print(f"Remaining files to work on: {len(filtered_files)}")
    print(f"Saved to: {filtered_output_file}")