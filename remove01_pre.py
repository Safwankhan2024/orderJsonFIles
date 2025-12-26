import re

def remove_prefixes_from_file(input_file, output_file=None, dry_run=False, encoding='utf-8'):
    """
    Remove numeric prefixes (01_, 02_, etc.) from filenames in a text file.
    Automatically handles encoding issues.
    """
    def try_read_file(file_path, encodings=['utf-8', 'latin-1', 'cp1252']):
        """Try reading the file with multiple encodings."""
        for enc in encodings:
            try:
                with open(file_path, 'r', encoding=enc) as f:
                    return f.readlines(), enc
            except UnicodeDecodeError:
                continue
        raise UnicodeDecodeError(f"Could not decode file with any of: {encodings}")
    
    try:
        # Try reading with multiple encodings
        lines, used_encoding = try_read_file(input_file)
        
        # Process each line
        processed_lines = []
        changes = []
        
        for i, line in enumerate(lines, 1):
            original = line.strip()
            new_name = re.sub(r'^\d+_', '', original)
            processed_lines.append(new_name + '\n')
            
            if original != new_name:
                changes.append((i, original, new_name))
        
        # Show results
        if changes:
            print(f"Encoding detected: {used_encoding}")
            print(f"Found {len(changes)} lines to modify:\n")
            for line_num, old, new in changes:
                print(f"  Line {line_num}: {old} → {new}")
        else:
            print("No lines with numeric prefixes found.")
            return
        
        # Save changes
        if not dry_run:
            output_path = output_file if output_file else input_file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.writelines(processed_lines)
            print(f"\n✓ Changes saved to: {output_path}")
        else:
            print("\n⚠️  This was a dry run. No changes were saved.")
            
    except FileNotFoundError:
        print(f"❌ Error: File '{input_file}' not found.")
    except Exception as e:
        print(f"❌ An error occurred: {e}")
        print("Try opening the file in a text editor and saving it as UTF-8.")

# Usage
if __name__ == "__main__":
    input_filename = "order.txt"  # Change to your file name
    print("\n=== Saving changes ===")
    remove_prefixes_from_file(input_filename, dry_run=False)