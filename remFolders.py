import os
import json

# Define the path to your output file
current_dir = os.path.dirname(os.path.abspath(__file__))
input_file = os.path.join(current_dir, "file_list_output.json")

# 1. Load the existing data
if not os.path.exists(input_file):
    print(f"Error: Could not find {input_file}. Please run your list script first.")
    exit()

with open(input_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

files = data.get("files", [])

# 2. Start Filtering
pattern = input("Enter the pattern (e.g., done_): ").strip()

# Step A: Identify all directories that contain a 'done' file
bad_dirs = set()
for f in files:
    basename = os.path.basename(f)
    dirname = os.path.dirname(f)
    if basename.startswith(pattern):
        bad_dirs.add(dirname)
        print(f"Found '{pattern}' in: {dirname}")

# Step B: Filter the list to exclude ANY file inside those directories
filtered_files = []
for f in files:
    # Use normalized path to avoid slash issues
    file_dir = os.path.dirname(f)
    
    is_in_bad_dir = False
    for bd in bad_dirs:
        # Check if the file is inside a bad directory or its subfolders
        # Using os.sep ensures we match "folder\file" correctly on Windows
        if bd == "": # File is in root
            if file_dir == "":
                is_in_bad_dir = True
                break
        elif f.startswith(bd + os.sep) or f.startswith(bd + "/"):
            is_in_bad_dir = True
            break
        elif f == bd: # The path itself is the directory
            is_in_bad_dir = True
            break
            
    if not is_in_bad_dir:
        filtered_files.append(f)

# 3. Save the results
data['files'] = filtered_files
data['filtered'] = True
data['filter_pattern'] = pattern

output_file = os.path.join(current_dir, "filtered_file_list_output.json")
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=4)

print(f"\nSuccessfully removed {len(files) - len(filtered_files)} file entries.")
print(f"Remaining files to work on: {len(filtered_files)}")
print(f"Filtered list saved to: {output_file}")