import os
import re
import requests
from tqdm import tqdm  # Importing tqdm for progress bar

# Base URL of the directory containing year-based folders
base_url = "http://jurisprudence.e-justice.tn/textes/pdf/juris/"

def get_directory_listing(url):
    print(f"Fetching directory listing from {url}")
    response = requests.get(url)
    response.raise_for_status()
    return response.text

def extract_year_folders(directory_text):
    # Find year-based folders (1959-2013)
    year_folders = re.findall(r'\b(19[5-9]\d|20[0-1]\d)/', directory_text)
    print(f"Found {len(year_folders)} year folders: {year_folders}")
    return year_folders

def extract_pdf_links(directory_text):
    # Find all .pdf files
    pdf_links = re.findall(r'href=["\'](.*?\.pdf)["\']', directory_text)
    print(f"Found {len(pdf_links)} PDFs")
    return pdf_links

def download_pdfs(pdf_links, year_url, save_path):
    os.makedirs(save_path, exist_ok=True)
    total_pdfs = len(pdf_links)  # Count the number of PDFs to download

    for pdf in tqdm(pdf_links, desc=f"Downloading PDFs in {os.path.basename(save_path)}", total=total_pdfs, unit="file"):
        pdf_url = year_url + pdf
        pdf_path = os.path.join(save_path, os.path.basename(pdf))

        if os.path.exists(pdf_path):
            print(f"File {pdf_path} already exists. Skipping...")
            continue

        print(f"Downloading {pdf_url}...")
        response = requests.get(pdf_url, stream=True)
        response.raise_for_status()

        with open(pdf_path, 'wb') as file:
            for chunk in response.iter_content(1024):
                file.write(chunk)

        print(f"Saved to {pdf_path}")

if __name__ == "__main__":
    print("Starting PDF download process...")
    directory_text = get_directory_listing(base_url)
    year_folders = extract_year_folders(directory_text)

    for year in year_folders:
        year_url = base_url + year + "/"
        save_path = os.path.join("../output/jurisprudence/pdfs/", year)

        print(f"Processing year {year}...")
        year_directory_text = get_directory_listing(year_url)
        pdf_links = extract_pdf_links(year_directory_text)

        if pdf_links:
            download_pdfs(pdf_links, year_url, save_path)
        else:
            print(f"No PDFs found in {year}")

    print("PDF download process completed.")
