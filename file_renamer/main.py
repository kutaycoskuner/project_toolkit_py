# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# ----- notes
# ----------------------------------------------------------------------------------------
'''
pip install ...

- use case
    - modification options
        - full name change with number 001          : <rename>
        - add prefix to name                        : <prefix>_name
        - full name change with unique identifier   : <id>
    
    - algorithm
        - set variable path     : ex. "C:\\users\\user\\desktop\\test"
        - set variable pattern  : ex. "*.txt"
        - apply one of three modification options

- todo
    - add optional date
    - add only suffix without name change
    - add id
'''
# ----------------------------------------------------------------------------------------
# ----- libraries
# ----------------------------------------------------------------------------------------
import os       # operating system
import re       # regular expression
import glob     # global: is a function that’s used to search for files that match a specific file pattern or name. It can be used to search CSV files and for text in files. 

# ----------------------------------------------------------------------------------------
# ----- variables
# ----------------------------------------------------------------------------------------
path                = ""
pattern             = "*"
rename_template     = "potatoes"
increment_decimal   = 3
prefix              = ""

# ----------------------------------------------------------------------------------------
# ----- functions
# ----------------------------------------------------------------------------------------
def change_full_name(path, file_list):
    for index, file_name in enumerate(file_list):
        file_path = os.path.join(path, file_name)
        if os.path.isfile(file_path):
            full_path_wo_extension, extension = os.path.splitext(file_name)
            old_name =  re.sub(re.escape(path), "", full_path_wo_extension)
            old_name = old_name[1:]
            # Construct the new full path for the renamed file
            iterator = f'{index+1:0{increment_decimal}}'

            if prefix != "":
                new_filename = f"{prefix}_{rename_template}_{iterator}{extension}"
            else:
                new_filename = f"{rename_template}_{iterator}{extension}"
            new_filepath = os.path.join(path, new_filename)

            # print(prefix, rename_template, iterator, extension)
            # print(file_path, new_filepath)            
            try:
                # Rename the file
                os.rename(file_path, new_filepath)
                print(f"\tOld: {file_name}")
                print(f"\tNew: {new_filepath}")
            except Exception as e:
                print(f"Error renaming {file_name}: {e}")

# ----------------------------------------------------------------------------------------
# ----- main
# ----------------------------------------------------------------------------------------
def main():
    # list files for correction
    # file_list = os.listdir(path)
    file_list = glob.glob(os.path.join(path, pattern))
    if not file_list or path == "":
        print("No path specified or no files found")
        return        
        
    print(path, "' :")
    for file in file_list:
        print(file)

    # ask confirmation for change:
    print("All files names going to be replaced with:", rename_template) 
    confirm = input("Are you sure you want to rename these files in this folder? (y/n): ")
    if confirm.lower() != 'y':
        print("Operation aborted.")
        return
    change_full_name(path, file_list)

# ----------------------------------------------------------------------------------------
# ----- start
# ----------------------------------------------------------------------------------------
if __name__ == "__main__":
    main()