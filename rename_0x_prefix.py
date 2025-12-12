import os

def rename_files_with_numbers(folder_path):
    # Get list of files in the directory, sorted alphabetically
    files = sorted(os.listdir(folder_path))

    for index, filename in enumerate(files, start=1):
        # Create new filename with leading number (2 digits)
        new_filename = f"{index:02d}_{filename}"

        # Full paths for old and new filenames
        old_filepath = os.path.join(folder_path, filename)
        new_filepath = os.path.join(folder_path, new_filename)

        # Rename the file
        os.rename(old_filepath, new_filepath)
        print(f"Renamed: {filename} -> {new_filename}")

# Example usage:
folder_path = "your_folder_path_here"  # Replace with your actual folder path
rename_files_with_numbers(folder_path)
