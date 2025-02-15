import fitz  # PyMuPDF
from pdf2image import convert_from_path
import pytesseract
from PIL import Image
from fpdf import FPDF
from bidi.algorithm import get_display  # For RTL text handling
from arabic_reshaper import reshape  # For reshaping Arabic text

def pdf_to_images(pdf_path):
    """
    Convert PDF pages to images.
    """
    images = convert_from_path(pdf_path)
    return images

def ocr_images_to_text(images):
    """
    Perform OCR on images to extract text.
    """
    text = ""
    for image in images:
        text += pytesseract.image_to_string(image, lang='ara')  # Use 'ara' for Arabic text
    return text

def create_pdf_from_text(text, output_pdf):
    """
    Create a new PDF from extracted text.
    """
    pdf = FPDF()
    pdf.add_page()
    pdf.add_font('Arial', '', 'arial.ttf', uni=True)  # Use a font that supports Arabic
    pdf.set_font('Arial', size=12) 
    reshaped_text = reshape(text)  # Reshape Arabic text
    bidi_text = get_display(reshaped_text)  # Apply RTL direction
    pdf.multi_cell(0, 10, bidi_text)  # Add text to PDF
    pdf.output(output_pdf)


def remove_watermark(input_pdf, output_pdf, watermark_text=None, watermark_image_bbox=None):
    """
    Remove watermark by extracting text using OCR and recreating the PDF.
    """
    # Step 1: Convert PDF to images
    images = pdf_to_images(input_pdf)
    
    # Step 2: Perform OCR on images to extract text
    text = ocr_images_to_text(images)
    
    # Step 3: Create a new PDF from the extracted text
    create_pdf_from_text(text, output_pdf)
    
    print(f"Watermark removed. Clean PDF saved to {output_pdf}")


  
def run():
   remove_watermark(
    input_pdf="input/54908.pdf",
    output_pdf="output/clean_cassation/54908.pdf"
   
    # watermark_image_bbox=(x0, y0, x1, y1)  # Uncomment and specify coordinates for image
)


if __name__ == "__main__":
    run()