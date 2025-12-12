def find_missing_filename(file1_path, file2_path):
    # Read the contents of both files
    with open(file1_path, 'r') as file1:
        filenames1 = set(file1.read().splitlines())

    with open(file2_path, 'r') as file2:
        filenames2 = set(file2.read().splitlines())

    # Find missing filenames in each direction
    missing_in_file1 = filenames2 - filenames1
    missing_in_file2 = filenames1 - filenames2

    return missing_in_file1, missing_in_file2

# Example usage (replace with your actual file paths)
file1_path = 'file1.txt'
file2_path = 'file2.txt'

missing_in_file1, missing_in_file2 = find_missing_filename(file1_path, file2_path)

print(f"Filenames in {file2_path} but missing in {file1_path}:")
for filename in missing_in_file1:
    print(filename)

print(f"\nFilenames in {file1_path} but missing in {file2_path}:")
for filename in missing_in_file2:
    print(filename)
