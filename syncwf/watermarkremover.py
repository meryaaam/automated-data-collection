import fitz  # PyMuPDF
from pdf2image import convert_from_path
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
from fpdf import FPDF
from bidi.algorithm import get_display  # For RTL text handling
from arabic_reshaper import reshape  # For reshaping Arabic text
import cv2
import numpy as np



def pdf_to_images(pdf_path):
    images = convert_from_path(pdf_path, dpi=300)  # Convert to images with high DPI
    return images


def preprocess_image(image):
    # Convert to grayscale
    image = image.convert('L')  # Convert to grayscale (L mode)
    
    # Step 1: Denoising (using Gaussian Blur)
    # Convert the image to an array for OpenCV processing
    image_np = np.array(image)
    image_np = cv2.GaussianBlur(image_np, (5, 5), 0)  # Apply Gaussian blur to reduce noise
    
    # Step 2: Adaptive Thresholding (enhance text contrast)
    # Adaptive thresholding to deal with different lighting and background
    image_np = cv2.adaptiveThreshold(image_np, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                     cv2.THRESH_BINARY, 11, 2)

    # Convert back to a PIL Image
    image = Image.fromarray(image_np)

    # Step 3: Sharpen the image to enhance text edges
    image = image.filter(ImageFilter.SHARPEN)  # Apply sharpening filter
    
    # Step 4: Enhance Contrast
    enhancer = ImageEnhance.Contrast(image)  # Enhance contrast
    image = enhancer.enhance(2)  # You can adjust the factor for better results
    
    # Step 5: Optionally, apply additional image enhancements
    # Further sharpening for more crisp edges (if needed)
    image = image.filter(ImageFilter.EDGE_ENHANCE_MORE)
    
    # Step 6: Optional: Rotate if text is tilted (use OCR detection for this)
    # This is an additional step if the image has rotational errors
    # For now, let's assume the text is correctly aligned.

    return image



def ocr_extract(image):
   
    custom_config = r'--oem 3 --psm 6'  
    ocr_data = pytesseract.image_to_string(image, lang='ara' , config=custom_config ,output_type=pytesseract.Output.STRING)  # Use 'ara' for Arabic text
   
    return ocr_data
     

def ocr_images_to_text(images):
    text = ""
    for image in images:
        image = preprocess_image(image)  # Preprocess the image before OCR
        text += ocr_extract(image)  # Use the detailed OCR extraction method
    return text

def create_pdf_from_text(text, output_pdf):
    pdf = FPDF()
    pdf.add_page()
    pdf.add_font('Amiri', '', 'font/amiri/Amiri-Regular.ttf', uni=True)  # Font for Arabic
    #pdf.add_font('Arial', '', 'font/arial/arial.ttf', uni=True)  # Font for French
    pdf.set_font('Amiri', size=12)
    #pdf.set_font('Arial', size=12)
    pdf.set_right_margin(10)
    reshaped_text = reshape(text)  # Reshape Arabic text for RTL direction
    bidi_text = get_display(reshaped_text)  # Apply right-to-left (RTL) direction
    pdf.multi_cell(0, 15, bidi_text, align='R')  # Add the text to the PDF
    pdf.output(output_pdf)

def remove_watermark(input_pdf, output_pdf):
    images = pdf_to_images(input_pdf)  # Convert PDF pages to images
    text = ocr_images_to_text(images)  # Perform OCR to extract text
    create_pdf_from_text(text, output_pdf)  # Create a PDF from the extracted text
    print(f"Watermark removed. Clean PDF saved to {output_pdf}")

def run():
    remove_watermark(input_pdf="input/24249.pdf", output_pdf="output/24249-3.pdf")

if __name__ == "__main__":
    run()
