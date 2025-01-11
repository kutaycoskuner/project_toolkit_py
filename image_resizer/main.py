# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# ----- notes
# ----------------------------------------------------------------------------------------
'''
- description
    This script batch resizes 4K textures to 2K textures using the Pillow library.
    It reads the folder paths for input and output from a .env file.

- metadata
    Author: Kutay Coskuner
    Version: 1.0
    Last Updated: 2025-01-12

- use case
    Useful for processing large sets of textures, commonly for game development or 3D projects.

- install
    - pip install pillow
    - pip install python-dotenv

- sources
    - https://pillow.readthedocs.io
    - https://github.com/theskumar/python-dotenv

- todo

'''
# ----------------------------------------------------------------------------------------
# ----- libraries
# ----------------------------------------------------------------------------------------
from PIL import Image
import os
from dotenv import load_dotenv

# ----------------------------------------------------------------------------------------
# ----- variables
# ----------------------------------------------------------------------------------------
# Load environment variables
load_dotenv()
INPUT_FOLDER = os.getenv("INPUT_FOLDER")  # Path to 4K textures
OUTPUT_FOLDER = os.getenv("OUTPUT_FOLDER")  # Path to save 2K textures
TARGET_SIZE = (2048, 2048)  # Resize target dimensions

# ----------------------------------------------------------------------------------------
# ----- functions
# ----------------------------------------------------------------------------------------
def resize_image(input_path, output_path, size):
    """
    Resize an image to the given size and save it.

    Args:
        input_path (str): Path to the input image.
        output_path (str): Path to save the resized image.
        size (tuple): Target dimensions (width, height).
    """
    with Image.open(input_path) as img:
        resized_img = img.resize(size, Image.Resampling.LANCZOS)
        resized_img.save(output_path)

def process_images(input_folder, output_folder, size):
    """
    Batch process images in the input folder and save them to the output folder.

    Args:
        input_folder (str): Path to the folder containing input images.
        output_folder (str): Path to the folder to save resized images.
        size (tuple): Target dimensions (width, height).
    """
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    for filename in os.listdir(input_folder):
        if filename.lower().endswith((".png", ".jpg", ".jpeg", ".tga")):
            input_path = os.path.join(input_folder, filename)
            output_path = os.path.join(output_folder, filename)
            resize_image(input_path, output_path, size)
            print(f"Resized: {filename} -> {output_path}")

# ----------------------------------------------------------------------------------------
# ----- main
# ----------------------------------------------------------------------------------------
def main():
    """
    Main function to handle the batch processing of textures.
    """
    if not INPUT_FOLDER or not OUTPUT_FOLDER:
        print("Error: INPUT_FOLDER and OUTPUT_FOLDER must be defined in the .env file.")
        return

    print(f"Processing images from {INPUT_FOLDER} to {OUTPUT_FOLDER}...")
    process_images(INPUT_FOLDER, OUTPUT_FOLDER, TARGET_SIZE)
    print("Batch resizing complete!")

# ----------------------------------------------------------------------------------------
# ----- start
# ----------------------------------------------------------------------------------------
if __name__ == "__main__":
    main()
