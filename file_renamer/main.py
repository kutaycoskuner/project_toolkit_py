# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# ----- notes
# ----------------------------------------------------------------------------------------
'''
pip install ...

- use case
    - modification options
        - [x] full name change with number 001          : <rename>
        - [x] add prefix to name                        : <prefix>_name
        - [x] make names all lowercase
        - [x] add/ change extension
        - full name change with unique identifier       : <id>
    
    - algorithm
        - set variable path     : ex. "C:\\users\\user\\desktop\\test"
        - set variable pattern  : ex. "*.txt"
        - apply one of three modification options

- todo
    - add optional date
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
work_folder_path         = ""
pattern                  = "*"
rename_template          = ""
increment_decimal        = 2
prefix                   = ""
should_change_names      = False
should_all_names_lower   = False
should_change_extension  = False
extension                = ".md"

# ----------------------------------------------------------------------------------------
# ----- functions
# ----------------------------------------------------------------------------------------
def get_name(old_name, extension, iterator) -> str:
    if prefix != "" and rename_template != "":
        new_filename = f"{prefix}_{rename_template}{iterator}{extension}"
    elif prefix != "" and rename_template == "":
        new_filename = f"{prefix}_{old_name}{extension}"
    elif rename_template != "":
        new_filename = f"{rename_template}_{iterator}{extension}"
    return new_filename

def lowercase_all_names(path, file_list) -> bool:
    for file_name in file_list:
        file_path = os.path.join(path, file_name)
        if os.path.isfile(file_path):
            full_path_wo_extension, extension = os.path.splitext(file_name)
            old_name = re.sub(re.escape(path), "", full_path_wo_extension)
            old_name = old_name[1:]

            new_filename = f"{old_name.lower()}{extension}"
            new_filepath = os.path.join(path, new_filename)

            try:
                # Rename the file
                print(f"\tOld: {file_path}")
                print(f"\tNew: {new_filepath}\n")
                os.rename(file_path, new_filepath)
            except Exception as e:
                print(f"Error renaming {file_name}: {e}")
                return False
    return True

def change_or_add_extension(path, file_list, new_extension) -> bool:
    print(f"\n\t ----- Changing extension ----- \n")
    for file_name in file_list:
        file_path = os.path.join(path, file_name)
        if os.path.isfile(file_path):
            full_path_wo_extension, extension = os.path.splitext(file_name)
            old_name = re.sub(re.escape(path), "", full_path_wo_extension)
            old_name = old_name[1:]

            # Check if the file already has an extension
            if not extension:
                new_filename = f"{old_name}{new_extension}"
            else:
                new_filename = f"{old_name}{new_extension}"

            new_filepath = os.path.join(path, new_filename)

            try:
                # Rename the file
                print(f"\tOld: {file_path}")
                print(f"\tNew: {new_filepath}\n")
                os.rename(file_path, new_filepath)
            except Exception as e:
                print(f"Error renaming {file_name}: {e}")
                return False
    return True

def display_change_before_confirm(path, file_list):
    if rename_template == "" and prefix == "":
        print("You need to give either rename template or prefix")
        return
    print("In path '", path, "'", len(file_list), "files found :")
    for index, file_name in enumerate(file_list):
        file_path = os.path.join(path, file_name)
        if os.path.isfile(file_path):
            full_path_wo_extension, extension = os.path.splitext(file_name)
            old_name =  re.sub(re.escape(path), "", full_path_wo_extension)
            old_name = old_name[1:]
            # Construct the new full path for the renamed file
            iterator = f'{index+1:0{increment_decimal}}'

            new_filename = get_name(old_name, extension, iterator)
                
            try:
                # Rename the file
                print(f"\tOld: {old_name}{extension}")
                print(f"\tNew: {new_filename}")
            except Exception as e:
                print(f"Error renaming {file_name}: {e}")

def change_full_name(path, file_list) -> bool:
    if rename_template == "" and prefix == "":
        print("You need to give either rename template or prefix")
        return
    for index, file_name in enumerate(file_list):
        file_path = os.path.join(path, file_name)
        if os.path.isfile(file_path):
            full_path_wo_extension, extension = os.path.splitext(file_name)
            old_name =  re.sub(re.escape(path), "", full_path_wo_extension)
            old_name = old_name[1:]
            # Construct the new full path for the renamed file
            iterator = f'{index+1:0{increment_decimal}}'

            new_filename = get_name(old_name, extension, iterator)
            new_filepath = os.path.join(path, new_filename)

            try:
                # Rename the file
                os.rename(file_path, new_filepath)
            except Exception as e:
                print(f"Error renaming {file_name}: {e}")
                return False
    return True

# ----------------------------------------------------------------------------------------
# ----- main
# ----------------------------------------------------------------------------------------
def main():
    # list files for correction
    # file_list = os.listdir(path)
    file_list = glob.glob(os.path.join(work_folder_path, pattern))
    if not file_list or work_folder_path == "":
        print("No path specified or no files found")
        return        
        
    # display_change_before_confirm(work_folder_path, file_list)

    # ask confirmation for change:
    confirm = input("Are you sure you want to rename these files in this folder? (y/n): ")
    if confirm.lower() != 'y':
        print("Operation aborted.")
        return
    if should_all_names_lower:
        lowercase_all_names(work_folder_path, file_list)
    if should_change_extension:
        change_or_add_extension(work_folder_path, file_list, extension)
    if should_change_names:
        if change_full_name(work_folder_path, file_list):
            print("Operation completed.")

# ----------------------------------------------------------------------------------------
# ----- start
# ----------------------------------------------------------------------------------------
if __name__ == "__main__":
    main()