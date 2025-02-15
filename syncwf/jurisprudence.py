import logging
import xml.etree.ElementTree as ET
import json
import requests
import os
import urllib3
from urllib.parse import urlparse
from requests.auth import HTTPBasicAuth
from bs4 import BeautifulSoup
import re
import sentry_sdk
from dotenv import load_dotenv
from datetime import datetime
from opensearchpy import OpenSearch
from pypdf import PdfReader
import json
from enum import Enum
from pathlib import Path
import typer
from rich.console import Console
from typing_extensions import Annotated
from typing import Optional
import time
from itertools import groupby
from operator import itemgetter
from langdetect import detect
from collections import defaultdict
from jsonschema import validate  
import csv
from collections import defaultdict


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


def process_file( log_level , creation_date , working_dir):
    
    csv_file_path = 'input/urls.txt.csv'
    
    url_pattern = r'(\d{4})/JURIS_(\d{4})_(\d{6})_(\d{4})_(\d{2})_(\d{2})\.pdf'
    # Initialize a dictionary to group information by doc_id
    grouped_urls = {} 
    
    # Use a set to track unique URLs and remove duplicates
    unique_urls = set()


    urls = []
    # Read the CSV file
    with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        
        # Iterate through each row in the CSV
        for row in reader:
            # Extract the URL from the third column (index 2)
            if len(row) > 2:
                url = row[2].strip()
            
                # Skip duplicate URLs
                if url in unique_urls:
                    continue
                unique_urls.add(url)

                match = re.search(url_pattern, url)
                if match:
                    year = match.group(1)
                    month = match.group(5)
                    day = match.group(6)
                    number = match.group(3) 
                    date = f"{day}/{month}/{year}"
                    doc_type = "jurisprudence"
                    doc_id = f"jurisprudence-{year}-{number}"
                    
                    # Append the URL along with its information (date, number, pdf) into the group
                    # grouped_urls[(date, number)].append({
                    #    'doc_type' : doc_type,
                    #    'doc_id' : doc_id,
                    #    'creation_date' : creation_date,
                    #    'articles' : [
                    #        {
                    #            'original_id' : 'idx',
                    #            'title' : '',
                    #            'lang': 'ar',
                    #            'categorie' : [] , 
                    #            'pdf_ar' : url , 
                    #            'content' : '',
                    #            'jort_year' : year,
                    #            'jort_number': number,
                    #            'page': 0 , 
                    #            'extras' : [] ,
                    #            'date_article': date,
                    #        }
                    #        
                    #    ]
                    #    
                    #})
                    # If the doc_id doesn't exist, initialize it
                    if doc_id not in grouped_urls:
                        grouped_urls[doc_id] = {
                            'doc_type': 'jurisprudence',
                            'doc_id': doc_id,
                            'creation_date': creation_date,
                            'articles': []
                        }
                    
                    # Append article details
                    grouped_urls[doc_id]['articles'].append({
                        'original_id': 'idx',
                        'title': '',
                        'lang': 'ar',
                        'categorie': [],
                        'pdf_ar': url,
                        'content': '',
                        'jort_year': year,
                        'jort_number': int(number),
                        'page': 0,
                        'extras': [],
                        'date_article': date,
                    })
    
    sorted_urls = sorted(urls) #sorted_urls = sorted(urls, reverse=True)

    #for (date, number), entries in grouped_urls.items():
    #    print(f"Date: {date}, Number: {number}")
    #    for entry in entries:
    #        print(f"  - PDF URL: {entry['pdf']}")

    grouped_urls_dict = dict(grouped_urls)

    # Write the grouped URLs to a JSON file
    with open('output/jurisprudence.json', 'w', encoding='utf-8') as jsonfile:
        json.dump(grouped_urls_dict, jsonfile, indent=4, ensure_ascii=False)

    print(f"Grouped URLs have been saved to output.json")

    


@app.command()
def process(
    pdf_path: Annotated[
        Path,
        typer.Argument(
            help="File or directory containing PDF(s) to process.",
        ),
    ],
    log_level: Annotated[
        LogLevel, typer.Option(help="Log level to use.")
    ] = LogLevel.INFO,
    creation_date: Annotated[
        Optional[int],
        typer.Option(
            help="Date to use for the metadata.",
        ),
    ] = int(time.time()),
    working_dir: Annotated[
        Optional[str],
        typer.Option(
            help="Working directory to store and process retrieved files.",
            envvar="WORKING_DIR",
        ),
    ] = os.getcwd(),
):
    """
    Process a Journal Officiel de la République Tunisienne (JORT) PDF file, extract articles,
    and save the extracted data to a JSON file.

    Args:
        pdf_path (str): The path to the JORT PDF file.
        creation_date (str): The creation date of the document.
        log_level (str): Log level to use.
        working_dir (str): The working directory to save the output.

    Raises:
        Exception: If failed to parse the document year.

    Returns:
        None
    """
    logger.setLevel(log_level.value)

    process_file( log_level , creation_date , working_dir)

    #
    #if pdf_path.is_file() and pdf_path.suffix == ".pdf":
    #    process_file(pdf_path , log_level , creation_date , working_dir)
    #elif pdf_path.is_dir():
    #    for file in pdf_path.iterdir():
    #         
    #        if file.suffix == ".pdf":
    #            logger.info(f"Found PDF: {file.name}")
    #            process_file(file , log_level , creation_date , working_dir)
    #else:
    #    raise ValueError("Invalid path: must be a JSON file or a directory containing JOSNS.")


def run():
    app()


if __name__ == "__main__":
    run()
