import json
import shutil
from pathlib import Path
import re

def clean_filename(text):
    """Clean disease name to make it safe for filenames."""
    # Replace spaces and special characters with underscores
    # Remove or replace characters that are invalid in filenames
    cleaned = re.sub(r'[<>:"/\\|?*\s]+', '_', text)
    # Remove multiple consecutive underscores
    cleaned = re.sub(r'_+', '_', cleaned)
    # Remove leading/trailing underscores
    cleaned = cleaned.strip('_')
    return cleaned.lower() + '.json'

def process_json_files(source_folder, target_subfolder='renamed_files'):
    """
    Check JSON files and rename them based on disease tag.
    
    Args:
        source_folder: Path to folder containing JSON files
        target_subfolder: Name of subfolder for renamed files
    """
    source_path = Path(source_folder)
    
    # Create target subfolder if it doesn't exist
    target_path = source_path / target_subfolder
    target_path.mkdir(exist_ok=True)
    
    # Counter for statistics
    stats = {'total': 0, 'correct': 0, 'renamed': 0, 'errors': 0}
    
    # Iterate through all JSON files
    for json_file in source_path.glob('*.json'):
        stats['total'] += 1
        try:
            # Read and parse JSON
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extract disease tag
            disease = data.get('disease')
            if not disease:
                print(f"⚠️  Skipping {json_file.name}: No 'disease' tag found")
                stats['errors'] += 1
                continue
            
            # Generate correct filename
            correct_filename = clean_filename(disease)
            current_filename = json_file.name
            
            # Compare filenames
            if current_filename.lower() == correct_filename:
                print(f"✅ {current_filename} - correct")
                stats['correct'] += 1
            else:
                # Create destination path
                destination = target_path / correct_filename
                
                # Handle duplicate filenames
                counter = 1
                original_dest = destination
                while destination.exists():
                    stem = original_dest.stem
                    destination = target_path / f"{stem}_{counter}.json"
                    counter += 1
                
                # Copy file to new location with correct name
                shutil.copy2(json_file, destination)
                print(f"🔄 {current_filename} -> {destination.name}")
                stats['renamed'] += 1
                
        except json.JSONDecodeError:
            print(f"❌ Error parsing {json_file.name}: Invalid JSON")
            stats['errors'] += 1
        except Exception as e:
            print(f"❌ Error processing {json_file.name}: {str(e)}")
            stats['errors'] += 1
    
    # Print summary
    print("\n" + "="*50)
    print("SUMMARY:")
    print(f"Total files processed: {stats['total']}")
    print(f"✅ Correctly named: {stats['correct']}")
    print(f"🔄 Renamed and moved: {stats['renamed']}")
    print(f"❌ Errors: {stats['errors']}")
    print(f"Destination folder: {target_path}")
    
    return stats

# Example usage:
if __name__ == "__main__":
    # Set your source folder path
    SOURCE_FOLDER = "./mcq_json"  # Change this to your actual folder path
    
    # Run the processing
    results = process_json_files(SOURCE_FOLDER)