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
import shutil
import uuid
from .constant import get_category_object


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


def process_pdf(file_path , lang ,  id ):

    if file_path: 
        if os.path.exists("output"+file_path):
            logger.info(f"Processing file: {file_path}") 
        else:
            logger.error(f"File not found: {file_path}")
    else:
        logger.error(f"No file provided for original_id : {id} lang: {lang}")


def get_pdf_path(output_prefix, pdf_filename):
    """ Vérifie si le fichier PDF existe et retourne son chemin, sinon journalise une erreur. """
    pdf_path = os.path.join(output_prefix, pdf_filename)
    if os.path.exists(pdf_path):
        return pdf_path
    else:
        logging.error(f"File not found: {pdf_path}")
        return None  # Retourne None si le fichier n'existe pas


def process_file(file_path , log_level , creation_date , working_dir ):

    
    with open(file_path, 'r') as file: 
        data = json.load(file)
   
    data_sorted = sorted(data, key=itemgetter('doc_id'))
    articles_data = {key: list(group) for key, group in groupby(data_sorted, key=itemgetter('doc_id'))}
    doc_type = os.path.splitext(os.path.basename(file_path))[0]

    structured_articles = []

    for doc_id, group in articles_data.items():  
        print(f"Doc ID: {doc_id}")   
        articles_list = []
        for article in group: 
            process_pdf(article['pdf_fr'] , 'fr' ,  article['original_id'])
            process_pdf(article['pdf_ar'] , 'ar' , article['original_id']) 

            category_object = get_category_object(article['categorie'])

            language = detect(article['content']) 
            logger.info("Content language:%s", language)
            original_id = article['original_id']
            year = article['jort_year']
            jort_number = article['jort_num']
            if not year :
                print(f"id {original_id}")
            if not jort_number :
                print(f"id {original_id}")
            year_num = f"{year}-{jort_number}"
            doc_id = f"{doc_type}-{year_num}"  
            output_prefix = f"output/{doc_type}/{year_num}/"
            json_filename = f"{doc_id}.json"
            pdf_ar= f"{doc_id}-ar.pdf"
            pdf_fr = f"{doc_id}-fr.pdf"
            file_ar = article['pdf_ar'] 
            file_fr = article['pdf_fr']
            lang = detect(article['content']) if article['content'] else ("fr" if article["lang"] == "fre" else article["lang"])
            structured_article = { 
                        "original_id": article['original_id'],
                        "title": "",
                        "lang": lang if lang in ["fr" , "ar"] else "fr",
                        "categorie": [category_object] if category_object else [{"slug": article['categorie']}],  # Ajout du tableau
                        "pdf_fr": os.path.join(output_prefix, pdf_fr) if file_fr else "",
                        "pdf_ar": os.path.join(output_prefix, pdf_ar) if file_ar else "",
                        "content": article['content'],
                        "jort_year": int(article["jort_year"]) if "jort_year" in article else None,
                        "jort_num": int(article['jort_num']),
                        "page": 0,
                        "date_article": article['date_article'],
                        "extras": {}
                       
                    } 
            articles_list.append(structured_article)

        category_object = get_category_object(article['categorie'])
        if article['pdf_content'] :
        
            structured_article = { 
            "original_id": f"idx{str(uuid.uuid4())[:5]}",
            "title": "",
            "lang":  lang if lang in ["fr" , "ar"] else "fr",
            "categorie": [category_object] if category_object else [{"slug": article['categorie']}], 
            "pdf_fr": os.path.join(output_prefix, pdf_fr)  if file_fr else "",
            "pdf_ar": os.path.join(output_prefix, pdf_ar)  if file_ar else "",
            "content": article['pdf_content'],
            "jort_year": int(article["jort_year"]) if "jort_year" in article else None,
            "jort_num": int(article['jort_num']),
            "page": 0,
            "date_article": article['date_article'],
            "extras": {}
                       
                    } 
            articles_list.append(structured_article)
        
        
        if article['pdf_content_ar'] :
            structured_article = { 
                "original_id": f"idx{str(uuid.uuid4())[:5]}",
                "title": "",
                "lang": lang if lang in ["fr" , "ar"] else "fr",
                "categorie": [category_object] if category_object else [{"slug": article['categorie']}],
                "pdf_fr": os.path.join(output_prefix, pdf_fr) if file_fr else "",
                "pdf_ar": os.path.join(output_prefix, pdf_ar) if file_ar else "",
                "content": article['pdf_content_ar'],
                "year": int(article["year"]) if "year" in article else None,
                "month": int(article["month"]) if "month" in article else None,
                "day": int(article["day"]) if "day" in article else None,
                "jort_year": int(article["jort_year"]) if "jort_year" in article else None,
                "jort_num": int(article['jort_num']),
                "page": 0,
                "date_article": article['date_article'],
                "extras": {}
                        
                        } 
            articles_list.append(structured_article)

        structured_articles.append({
            "doc_type": doc_type,
            "doc_id": doc_id,
            "creation_date": creation_date,
            "ministry": group[0]['ministry'],  # Take ministry from the first article in the group
            "articles": articles_list  # Store the list of articles
        })   

        output_dest_dir = os.path.join(working_dir, output_prefix)
        doc = dict(
            doc_type= doc_type,
            doc_id=doc_id,
            creation_date=creation_date,
            articles=articles_list,
        )
        validate(instance=doc, schema=json.load(open("./schema.json")))

        os.makedirs(output_dest_dir, exist_ok=True)
        output_json = os.path.join(output_dest_dir, json_filename)
        with open(output_json, "w", encoding="utf-8") as json_file:
            json.dump(doc, json_file, ensure_ascii=False, indent=4)
        
        if file_ar : 
            shutil.copy('output'+file_ar, os.path.join(output_dest_dir, pdf_ar))
        if file_fr : 
            shutil.copy('output'+file_fr, os.path.join(output_dest_dir, pdf_fr))
      


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

    
    if pdf_path.is_file() and pdf_path.suffix == ".json":
        process_file(pdf_path , log_level , creation_date , working_dir)
    elif pdf_path.is_dir():
        for file in pdf_path.iterdir():
             
            if file.suffix == ".json":
                logger.info(f"Found JSON: {file.name}")
                process_file(file , log_level , creation_date , working_dir)
    else:
        raise ValueError("Invalid path: must be a JSON file or a directory containing JOSNS.")


def run():
    app()


if __name__ == "__main__":
    run()
