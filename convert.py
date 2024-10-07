import os
import json

def scan_folder(folder_path):
    # Dictionary to store file data
    file_data = {}

    # Folders and files to exclude
    excluded_folders = {'venv', '_pycache_'}
    excluded_files = {'convert.py', 'requirements.txt', 'finance.db'}

    # Walk through all subdirectories and files
    for subdir, dirs, files in os.walk(folder_path):
        # Exclude specific directories by modifying `dirs` in-place
        dirs[:] = [d for d in dirs if d not in excluded_folders]
        
        for file in files:
            # Skip excluded files
            if file in excluded_files:
                continue

            # Check file extensions
            if file.endswith(('.html', '.css', '.js', '.py')):
                file_path = os.path.join(subdir, file)
                
                # Read the file content
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    # Store the content in the dictionary with the relative path as the key
                    relative_path = os.path.relpath(file_path, folder_path)
                    file_data[relative_path] = content
                    print(f"Successfully read {file_path}")
                except Exception as e:
                    print(f"Failed to read {file_path}: {e}")
    
    return file_data

def save_to_json(file_data, output_file):
    # Save the collected file data to a JSON file
    try:
        with open(output_file, 'w', encoding='utf-8') as json_file:
            json.dump(file_data, json_file, indent=4)
        print(f"Data successfully saved to {output_file}")
    except Exception as e:
        print(f"Failed to save data to {output_file}: {e}")

# Specify the folder to scan and the output JSON file name
folder_to_scan = r'C:\Users\Owner\Documents\Personal Projects\Finance'
output_json_file = 'compiled_files.json'

# Scan the folder and save the data to a JSON file
file_contents = scan_folder(folder_to_scan)
save_to_json(file_contents, output_json_file)
