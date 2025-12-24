import os
import shutil
import fnmatch

# ---------------------------------------------
# CONFIGURATION (edit these manually)
# ---------------------------------------------
MAIN_FOLDER = r"mcq_json"
IGNORE_PATTERN = "*review*"     # Example: ignore files containing "temp"
# You can use wildcards: "*.txt", "*_backup.*", "*draft*"


# ---------------------------------------------
# SCRIPT LOGIC
# ---------------------------------------------
def copy_files_ignoring_pattern(main_folder, ignore_pattern):
    for root, dirs, files in os.walk(main_folder):
        # Skip the main folder itself
        if root == main_folder:
            continue

        for file in files:
            # Skip files matching the ignore pattern
            if fnmatch.fnmatch(file, ignore_pattern):
                print(f"Skipping (pattern match): {file}")
                continue

            src_path = os.path.join(root, file)
            dst_path = os.path.join(main_folder, file)

            # If a file with same name exists, rename to avoid overwrite
            if os.path.exists(dst_path):
                base, ext = os.path.splitext(file)
                counter = 1
                new_name = f"{base}_{counter}{ext}"
                new_dst = os.path.join(main_folder, new_name)

                while os.path.exists(new_dst):
                    counter += 1
                    new_name = f"{base}_{counter}{ext}"
                    new_dst = os.path.join(main_folder, new_name)

                dst_path = new_dst

            print(f"Copying: {src_path} → {dst_path}")
            shutil.copy2(src_path, dst_path)


if __name__ == "__main__":
    copy_files_ignoring_pattern(MAIN_FOLDER, IGNORE_PATTERN)
    print("\nDone.")
