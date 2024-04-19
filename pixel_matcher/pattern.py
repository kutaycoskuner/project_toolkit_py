# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# ----- notes
# ----------------------------------------------------------------------------------------
'''
- description

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
work_folder =  "C:\\Users\\kutay\\OneDrive\\Documents\\GitHub\\project_toolkit_py\\pixel_matcher\\work_folder"

img1_file_name = 'base.png'
img2_file_name = 'diff.png'

img1_file_path = os.path.join(work_folder, img1_file_name)
img2_file_path = os.path.join(work_folder, img2_file_name)

# ----------------------------------------------------------------------------------------
# ----- functions
# ----------------------------------------------------------------------------------------
def compare_images(image1_path, image2_path):
    # Read the images
    image1 = cv2.imread(img1_file_path)
    image2 = cv2.imread(img2_file_path)
    
    # Check if the images have the same dimensions
    if image1.shape != image2.shape:
        print("Images have different dimensions")
        return
    
    # Compare each pixel
    height, width, _ = image1.shape
    difference = 0
    for y in range(height):
        for x in range(width):
            # Compare pixel RGB values
            pixel1 = image1[y, x]
            pixel2 = image2[y, x]
            if not all(pixel1 == pixel2):
                difference += 1
    
    # Calculate percentage difference
    total_pixels = height * width
    percentage_difference = (difference / total_pixels) * 100
    
    return percentage_difference

# ----------------------------------------------------------------------------------------
# ----- main
# ----------------------------------------------------------------------------------------
def main():
    difference_percentage = compare_images(img1_file_path, img2_file_path)
    print("Percentage difference:", difference_percentage)

# ----------------------------------------------------------------------------------------
# ----- start
# ----------------------------------------------------------------------------------------
if __name__ == "__main__":
    main()