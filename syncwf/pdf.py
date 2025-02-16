import tkinter
from tkinter import *
import tkinter as tk
import tkinter.messagebox as mbox
from tkinter import ttk
from tkinter import filedialog
from PIL import ImageTk, Image
import cv2
import skimage.filters as filters
import numpy as np
import cv2 
from matplotlib import pyplot as plt
import img2pdf
 

def remove_watermark(image_path, output_path, watermark_location, threshold=200):
 
    # Load the image
    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)

    # Apply Fourier Transform to the image
    f = np.fft.fft2(image)
    fshift = np.fft.fftshift(f)

    # Create a mask to filter out the watermark (high-frequency components)
    rows, cols = image.shape
    crow, ccol = rows // 2, cols // 2
    mask = np.ones((rows, cols), np.uint8)
    r = 30  # Radius of the mask (adjust based on watermark size)
    mask[crow - r:crow + r, ccol - r:ccol + r] = 0

    # Apply the mask to the Fourier-transformed image
    fshift_filtered = fshift * mask

    # Inverse Fourier Transform to get the filtered image
    f_ishift = np.fft.ifftshift(fshift_filtered)
    image_filtered = np.fft.ifft2(f_ishift)
    image_filtered = np.abs(image_filtered)

    # Normalize the filtered image
    image_filtered = cv2.normalize(image_filtered, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)

    # Use adaptive thresholding to detect the remaining watermark
    thresh = cv2.adaptiveThreshold(image_filtered, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)

    # Find contours of the watermark
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Create a mask for the watermark
    mask = np.zeros_like(image)
    for contour in contours:
        if cv2.contourArea(contour) > 100:  # Filter out small contours
            cv2.drawContours(mask, [contour], -1, 255, -1)

    # Inpaint the watermark regions
    result = cv2.inpaint(image, mask, inpaintRadius=3, flags=cv2.INPAINT_TELEA)

    # Save the result
    cv2.imwrite('image-after.jpeg', result)

    # Display the results
    plt.figure(figsize=(12, 6))
    plt.subplot(1, 3, 1), plt.imshow(image, cmap='gray'), plt.title('Original Image')
    plt.subplot(1, 3, 2), plt.imshow(image_filtered, cmap='gray'), plt.title('Filtered Image')
    plt.subplot(1, 3, 3), plt.imshow(result, cmap='gray'), plt.title('Final Result')
    plt.show()

def remove_red_watermark(image_path, output_path, lower_red, upper_red, inpaint_radius=3):
    # Load the image in color
    image = cv2.imread(image_path)
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)  # Convert to RGB for display

    # Convert the image to HSV color space for better color segmentation
    hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    # Define the range for red color in HSV
    # Note: Red spans two ranges in HSV due to the circular nature of the hue channel
    lower_red1 = np.array([0, 50, 50])  # Lower range for red
    upper_red1 = np.array([10, 255, 255])  # Upper range for red
    lower_red2 = np.array([170, 50, 50])  # Lower range for red (wraps around)
    upper_red2 = np.array([180, 255, 255])  # Upper range for red

    # Create masks for the red color ranges
    mask1 = cv2.inRange(hsv_image, lower_red1, upper_red1)
    mask2 = cv2.inRange(hsv_image, lower_red2, upper_red2)
    red_mask = cv2.bitwise_or(mask1, mask2)  # Combine both masks

    # Optionally, dilate the mask to ensure the watermark is fully covered
    kernel = np.ones((3, 3), np.uint8)
    red_mask = cv2.dilate(red_mask, kernel, iterations=1)

    # Inpaint the watermark regions
    result = cv2.inpaint(image, red_mask, inpaintRadius=inpaint_radius, flags=cv2.INPAINT_TELEA)

    # Save the result
    cv2.imwrite(output_path, result)

    # Display the results
    plt.figure(figsize=(12, 6))
    plt.subplot(1, 3, 1), plt.imshow(image_rgb), plt.title('Original Image')
    plt.subplot(1, 3, 2), plt.imshow(red_mask, cmap='gray'), plt.title('Red Watermark Mask')
    plt.subplot(1, 3, 3), plt.imshow(cv2.cvtColor(result, cv2.COLOR_BGR2RGB)), plt.title('Final Result')
    plt.show()

def image_to_pdf(image_path, output_pdf_path):
    # Convert the image to PDF
    with open(output_pdf_path, "wb") as pdf_file:
        pdf_file.write(img2pdf.convert(image_path))

def run():
    input_pdf = "input/54908.pdf"  # Remove the comma to avoid creating a tuple
    output_pdf = "output/clean_cassation/54908.pdf"  # Same here

    image_path = "output/img1.jpg"
    output_path = "output/image1-1.jpg"
    watermark_location = (100, 100, 200, 50)  # (x, y, width, height) of the watermark
    remove_red_watermark(image_path,
    output_path='image_after_removal.jpeg',
    lower_red=np.array([0, 50, 50]),  # Adjust these values based on the watermark color
    upper_red=np.array([10, 255, 255]))
    
    image_to_pdf(input_pdf ,output_path )
    # List the PDF files in the CWD

   # exitb.place(x=700, y = 550)
   # exitb=Button(window1, text="EXIT",command=exit_win1,  font=("Arial", 25), bg = "red", fg = "blue")
   # window1.protocol("WM_DELETE_WINDOW", exit_win1)
   # window1.mainloop()
        
 
if __name__ == "__main__":
    run()

 