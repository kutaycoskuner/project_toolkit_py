# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# ----- notes
# ----------------------------------------------------------------------------------------
'''
- description
    - compares two images in a in a folder by adress and presents if there is difference amongst them
    - folder: work_folder
        - images 

- metadata

- use case

- install
    - pip install numpy
    - pip install opencv-python

- todo

'''
# ----------------------------------------------------------------------------------------
# ----- libraries
# ----------------------------------------------------------------------------------------
import os       # operating system
import cv2
import numpy as np

# ----------------------------------------------------------------------------------------
# ----- variables
# ----------------------------------------------------------------------------------------
work_folder = "C:\\Users\\kutay\\OneDrive\\Documents\\GitHub\\study_opengl\\opengl_renderer\data\\test_scene_frames"
# "C:\\Users\\kutay\\OneDrive\\Documents\\GitHub\\project_toolkit_py\\pixel_matcher\\work_folder"

# img1_file_name = 'base.png'
# img2_file_name = 'diff.png'

pattern_file_name = 'pattern2.jpg'
find_file_name    = 'find_pattern3.jpg'

# img1_file_path = os.path.join(work_folder, pattern_file_name)
# img2_file_path = os.path.join(work_folder, find_file_name)

tolerance_limit = 60


# ----------------------------------------------------------------------------------------
# ----- functions
# ----------------------------------------------------------------------------------------
def calc_tolerance(pixel1, pixel2) -> int:
    tolerance    = 0
    tolerance    = abs(int(pixel1[0]) - int(pixel2[0]))
    tolerance   += abs(int(pixel1[1]) - int(pixel2[1]))
    tolerance   += abs(int(pixel1[2]) - int(pixel2[2]))
    return tolerance

def compare_images(image1_path, image2_path) -> bool:
    # Read the images
    pattern = cv2.imread(image1_path)
    search = cv2.imread(image2_path)
    
    if (pattern.any() == None or search.any() == None):
        print(pattern)
        return
    # Compare each pixel
    search_height, search_width, _ = search.shape
    p_height, p_width, _ = pattern.shape
    difference = 0
    for y in range(search_height-p_height+1):
        for x in range(search_width-p_width+1):
            # Compare pixel RGB values
            pixel1 = pattern[0, 0]
            pixel2 = search[y, x]
            # try to negate 
            if calc_tolerance(pixel1, pixel2) < tolerance_limit:
                exists = True
                for k in range(p_height):
                    for i in range(p_width):
                        pixel1 = pattern[k, i]
                        pixel2 = search[y+k, x+i]
                        if calc_tolerance(pixel1, pixel2) > tolerance_limit:
                            exists = False
                            break
                    if not exists:
                        break
                # if not negated
                if exists:
                    print("starting at: ", y, x)
                    return True
    return False
    
    # Calculate percentage difference
    total_pixels = search_height * search_width
    percentage_difference = (difference / total_pixels) * 100
    
    return percentage_difference

def count_files_in_directory(directory) -> int:
    # List all entries in the directory
    entries = os.listdir(directory)
    
    # Filter out only files
    files = [entry for entry in entries if os.path.isfile(os.path.join(directory, entry))]
    
    return len(files)

# ----------------------------------------------------------------------------------------
# ----- main
# ----------------------------------------------------------------------------------------
def main():
    test_count = int(count_files_in_directory(work_folder)/2)
    for i in range(test_count):
        img1_file_path = os.path.join(work_folder, "scene" + str(i) + "_base.png")
        img2_file_path = os.path.join(work_folder, "scene" + str(i) + "_test.png")
        difference_percentage = compare_images(img1_file_path, img2_file_path)
        print("Scene", i," pixel matching:", difference_percentage)

# ----------------------------------------------------------------------------------------
# ----- start
# ----------------------------------------------------------------------------------------
if __name__ == "__main__":
    main()