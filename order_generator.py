import os
from datetime import datetime

def generate_order_file(folder_path):
    # Get list of all JSON files in the folder
    json_files = [f for f in os.listdir(folder_path) if f.endswith('.json')]

    # Sort the files alphabetically
    json_files.sort()

    # Create order.txt file in the same directory as the JSON files
    order_file_path = os.path.join(folder_path, 'order.txt')
    with open(order_file_path, 'w') as order_file:
        for index, filename in enumerate(json_files, start=1):
            # Format the line as specified (01_filename.json)
            formatted_line = f"{index:02d}_{filename}"
            order_file.write(formatted_line + '\n')

    return order_file_path

def save_ordered_files(folder_path, ordered_filenames):
    # Generate a new filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    new_filename = f"ordered_{timestamp}.txt"
    new_file_path = os.path.join(folder_path, new_filename)

    # Write the ordered filenames to the new file
    with open(new_file_path, 'w') as new_file:
        for filename in ordered_filenames:
            new_file.write(filename + '\n')

    return new_file_path
