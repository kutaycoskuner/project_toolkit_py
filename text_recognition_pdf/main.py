# ----------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------
# ----- notes
# ----------------------------------------------------------------------------------------
'''
- description
    - pdf text recognition to .txt
    - work_folder contains a .pdf file extract the content and presents it on .txt file with the same name

- metadata

- use case

- install
    - pip install pytesseract
    - pip install pypdf
    - pip install Pillow
    - pip install python-poppler

- sources
    - https://www.geeksforgeeks.org/extract-text-from-pdf-file-using-python/
    - https://pypi.org/project/pytesseract/
    - https://pillow.readthedocs.io/

- todo

'''
# ----------------------------------------------------------------------------------------
# ----- libraries
# ----------------------------------------------------------------------------------------
import fitz  # PyMuPDF
from pypdf import PdfReader 
import os
from PIL import Image
import pytesseract
from pdf2image import convert_from_path
import re

# ----------------------------------------------------------------------------------------
# ----- variables
# ----------------------------------------------------------------------------------------
pytesseract.pytesseract.tesseract_cmd = r'C:\\Users\\kutay\AppData\\Local\\Programs\\Tesseract-OCR\\tesseract.exe'
input_folder = "_hidden/"
output_folder = '_hidden/'
temp_folder = output_folder + '_temp/'

input_path = work_folder + 'lv1.pdf'
output_file_name = os.path.splitext(os.path.basename(input_path))[0] + '.md'
output_path = os.path.join(output_folder, output_file_name)


# ----------------------------------------------------------------------------------------
# ----- functions
# ----------------------------------------------------------------------------------------
def natural_sort_key(s):
    return [int(text) if text.isdigit() else text.lower() for text in re.split('(\d+)', s)]

def ocr_pdf(file_path):
    # Convert PDF to images
    pages = convert_from_path(file_path,)
    
    # Extract text from each image
    text = ""
    for page in pages:
        text += pytesseract.image_to_string(page)
    return text

def pdf_to_jpg(pdf_path, output_folder):
    # Create the output folder if it does not exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    # Open the PDF file
    pdf_document = fitz.open(pdf_path)
    
    for page_num in range(len(pdf_document)):
        # Load each page
        page = pdf_document.load_page(page_num)
        
        # Convert page to pixmap (image)
        pix = page.get_pixmap()
        
        # Create an image object from pixmap
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        
        # Define the output path for each image
        output_path = os.path.join(output_folder, f"page_{page_num + 1}.jpg")
        
        # Save the image as JPG
        img.save(output_path, "JPEG")
        print(f"Saved {output_path}")

def ocr_jpg_files(input_folder, output_file_path):
    # List all files in the input folder
    files = os.listdir(input_folder)
    # Sort files using natural sort
    files.sort(key=natural_sort_key)
    combined_text = ""
    for file in files:
        if file.lower().endswith('.jpg'):
            image_path = os.path.join(input_folder, file)
            img = Image.open(image_path)
            text = pytesseract.image_to_string(img)
            combined_text += text + "\n\n"
            print(f"Extracted text from {file}")

    return combined_text
    
    print(f"All extracted text saved to {output_file_path}")

def remove_temp_folder(input_folder):
    # Remove the temp folder and its contents
    if os.path.exists(input_folder):
        for file in os.listdir(input_folder):
            os.remove(os.path.join(input_folder, file))
        os.rmdir(input_folder)
        print(f"Deleted temporary folder {input_folder}")

# ----------------------------------------------------------------------------------------
# ----- main
# ----------------------------------------------------------------------------------------
def main():
    # Check if file exists and is a PDF
    if not os.path.isfile(input_path):
        print(f"File {input_path} does not exist.")
        return
    
    if not input_path.lower().endswith('.pdf'):
        print(f"File {input_path} is not a PDF.")
        return

    # Creating a PDF reader object 
    reader = PdfReader(input_path) 
    
    # Extracting text from all pages
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text
        else:
            # Perform OCR on the page if text extraction fails
            pdf_to_jpg(input_path, temp_folder)
            text += ocr_jpg_files(temp_folder, output_folder)
            remove_temp_folder(temp_folder)
            break  # Assume all pages are images if one is detected

    # Writing text to .md file
    with open(output_path, 'w', encoding='utf-8') as file:
        file.write(text)
    print(f"Text extracted and saved to {output_path}")


# ----------------------------------------------------------------------------------------
# ----- start
# ----------------------------------------------------------------------------------------
if __name__ == "__main__":
    main()
