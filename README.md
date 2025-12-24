Drag and Drop:
How to Use the Enhanced Application:
Run the GUI: Execute order_gui.py to launch the application.
Select Folder: Click "Select Folder" and choose the directory containing your JSON files.
Drag to Reorder:
Click and hold on an item in the listbox.
Drag it up or down to reorder.
Release the mouse button when satisfied with the new position.
Generate Order File: Once you're done reordering, click "Generate Order File" to create a new ordered file with a timestamp prefix.

Compare files:
How to use this script:
Save the script to a Python file (e.g., compare_filenames.py)
Replace 'list1.txt' and 'list2.txt' with the paths to your actual text files
Run the script using Python: python compare_filenames.py
The script will output:
Filenames that are in the second file but missing from the first file
Filenames that are in the first file but missing from the second file
This should help you identify which filename is missing between your two text files.

Rename files to start with 01_, 02_ prefix in a folder according to alphabetical order:
To use this script:
Save it to a Python file (e.g., rename_files.py)
Replace "your_folder_path_here" with the actual path to your folder containing the JSON files
Run the script: python rename_files.py
The script will:
List all files in the directory alphabetically
Rename each file with a leading 2-digit number (01, 02, 03, etc.)
Maintain the original filename after the number
Print out what it renamed for verification

checkbyAI
it is using deepseek and good prompt, it will iterate same folder and same mcq style and same naming convention

makedocxv11
it will make a nice docx from the folder

makemd
this is making a markdown

missingfile
to compare two txt files to find a missing file

order_generator and gui
drag and drop custom order, it will be read by the makemd and makedocx

rename
it will name all files in a folder to _01_ or _02_ etc

sample mcqs
generate mcqs in this format to be useful

listfilename:
python script will give a file name in json for all folder and sub folders.
rem folder:
then read the output and remove folder instances having the specific file name pattern.

added check mcqs:
the env file should be changed to .env and then add key without quotes and then run checkmcqs, the folder path can be set inside and the openai model can also be set, it is now gpt-5.1

extract:
it will copy all files from subfolder into main folder and it will ignore the file having a defined name pattern. This pattern can be defined in the script.


