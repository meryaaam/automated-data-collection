import logging
import requests
from bs4 import BeautifulSoup
import typer
from enum import Enum
from rich.console import Console
from dotenv import load_dotenv
import sentry_sdk
import os
import urllib3
import time
from typing_extensions import Annotated
from pathlib import Path
from typing import Optional
from urllib.parse import quote
import json
import urllib.parse
import fitz 




class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    ERROR = "ERROR"


logging.basicConfig(format="%(asctime)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

console = Console()

app = typer.Typer(help="Legaldoc Workflow - fetching and parsing tools.")

load_dotenv()

sentry_sdk.init(
    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for performance monitoring.
    traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", 0.3)),
    # Set profiles_sample_rate to 1.0 to profile 100%
    # of sampled transactions.
    # We recommend adjusting this value in production.
    profiles_sample_rate=float(os.getenv("SENTRY_PROFILES_SAMPLE_RATE", 0.3)),
)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logging.basicConfig(filename='log.txt', level=logging.INFO,
                    format='%(asctime)s - %(message)s')


def extract_pdf_text(pdf_path):
    doc = fitz.open(pdf_path)
    pages = []
    
    for page_num in range(len(doc)):
        text = doc[page_num].get_text("text")  # Keep text formatting
        pages.append({
            "page_number": page_num + 1,
            "content": text
        })
    
    return pages

def remove_watermark(pdf_path, output_pdf):
    doc = fitz.open(pdf_path)

    for page in doc:
        for image in page.get_images(full=True):
            xref = image[0]
            page.delete_image(xref)  # Remove image-based watermarks
            
        # Try to remove text-based watermarks
        for annot in page.annots():
            page.delete_annot(annot)

    # Save the cleaned PDF
    doc.save(output_pdf)
    print(f"Cleaned PDF saved as: {output_pdf}")

    # Example usage
  

def process_file( log_level , creation_date ):
    
    url = "http://www.cassation.tn/%D9%81%D9%82%D9%87-%D8%A7%D9%84%D9%82%D8%B6%D8%A7%D8%A1/?tx_uploadexample_piexample%5Baction%5D=list&tx_uploadexample_piexample%5Bcontroller%5D=Example&cHash=ec357dd81b970f1852dd711d37d8430f"

    payload = {
        "tx_uploadexample_piexample[__referrer][@extension]": "UploadExample",
        "tx_uploadexample_piexample[__referrer][@vendor]": "Helhum",
        "tx_uploadexample_piexample[__referrer][@controller]": "Example",
        "tx_uploadexample_piexample[__referrer][@action]": "search",
        "tx_uploadexample_piexample[__referrer][arguments]": "YTowOnt9559a7930340573df307f1674a0953b17e7dcee55",
        "tx_uploadexample_piexample[__trustedProperties]": 'a:1:{s:6:"search";a:5:{s:9:"shkeyword";i:1;s:10:"shdocdate1";i:1;s:10:"shdocdate2";i:1;s:8:"shdocnum";i:1;s:7:"shtheme";i:1;}}',
        "tx_uploadexample_piexample[search][shkeyword]": "",
        "tx_uploadexample_piexample[search][shdocdate1]": "",
        "tx_uploadexample_piexample[search][shdocdate2]": "",
        "tx_uploadexample_piexample[search][shdocnum]": "",
        "tx_uploadexample_piexample[search][shtheme]": ""
    }

    headers = {
        'Content-Type': 'multipart/form-data; boundary=----WebKitFormBoundaryyGZKbgGnYHNLEdCc',
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        'Referer': 'http://www.cassation.tn/%D9%81%D9%82%D9%87-%D8%A7%D9%84%D9%82%D8%B6%D8%A7%D8%A1/'
    }

    input_html = 'input/stored_page.html'
    
   

    try:
        response = requests.post(url, data=payload, headers=headers)
        response.raise_for_status()  # Raise an error for bad status codes
        html_content = response.text
        if "Oops, an error occurred!" in html_content:
            print("Error occurred")
            if os.path.exists(input_html):
                with open(input_html, "r", encoding="utf-8") as file:
                    html_content = file.read()
    
    
        else: 
            print("Successfully retrieved the body!")
             
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")

    
    pdf_path = "document.pdf"
    input_pdf = "input/54908.pdf"  # Replace with your file path
    output_pdf = "output/clean_cassation/c_54908.pdf"
    remove_watermark(input_pdf, output_pdf)

    if html_content:
        extracted_data = []
        soup = BeautifulSoup(html_content, 'html.parser')
        div = soup.find('div', class_='tx-upload-example') 
        if div:
            # Now find the table inside this div
            table = div.find("table", class_="filter")  # Ensure class name matches 
            if table:
                tbody = table.find("tbody")
                if tbody:
                    rows = tbody.find_all("tr")
                    for row in rows:
                        cols = row.find_all("td")
                        if len(cols) >= 4:  # Ensure there are enough columns
                            decision_number = cols[0].text.strip() 
                            date = cols[1].text.strip()
                            subject = cols[2].find("a").text.strip() if cols[2].find("a") else "No subject"
                            subject = subject.replace("\n", " ").strip() 
                            subject_link = urllib.parse.unquote(cols[2].find("a")["href"]) if cols[2].find("a") else "No link"
                            pdf_link = urllib.parse.unquote(cols[3].find("a")["href"]) if cols[3].find("a") else "No PDF"
                            #print(f"رقم القرار: {decision_number}")
                            #print(f"التاريخ: {date}")
                            #print(f"الموضوع: {subject}")
                            #print(f"رابط الموضوع: {subject_link}")
                            #print(f"رابط PDF: {pdf_link}")
                            #print("-" * 50)
                            row_data = {
                                "decision_number": decision_number,
                                "date": date,
                                "subject": subject,
                                "subject_link": subject_link,
                                "pdf_link": pdf_link
                            }
                            extracted_data.append(row_data)
                            with open("output/cassation.json", "w", encoding="utf-8") as json_file:
                                json.dump(extracted_data, json_file, ensure_ascii=False, indent=4)
                        else:
                            print("Skipping row with insufficient columns.")
                else:
                    print("Table found, but no tbody present.")
            else:
                print("Table not found inside the div!")
        else:
            print("Div with class 'scn-12' not found in the response!")
    else:
        print("No HTML content available for processing.")


@app.command()
def process(
     
    log_level: Annotated[
        LogLevel, typer.Option(help="Log level to use.")
    ] = LogLevel.INFO,
    creation_date: Annotated[
        Optional[int],
        typer.Option(
            help="Date to use for the metadata.",
        ),
    ] = int(time.time()),
    
):
    """
    Process a Journal Officiel de la République Tunisienne (JORT) PDF file, extract articles,
    and save the extracted data to a JSON file.

    Args:
       
        creation_date (str): The creation date of the document.
        log_level (str): Log level to use.
         

    Raises:
        Exception: If failed to parse the document year.

    Returns:
        None
    """
    logger.setLevel(log_level.value)

    process_file( log_level , creation_date )

    

def run():
    app()


if __name__ == "__main__":
    run()
