import requests
from bs4 import BeautifulSoup
import json
import os
from urllib.parse import urlparse
import threading
def log_message(message, log_file='cassasion_log.txt'):
    with open(log_file, 'a') as file:
        file.write(message + '\n')
def save_json(data, category, original_id):
    # Create the directory if it doesn't exist
    directory = os.path.join('output_json', category)
    os.makedirs(directory, exist_ok=True)

    # Define the file path
    file_path = os.path.join(directory, f"{original_id}.json")

    # Save the JSON data to the file
    with open(file_path, 'w', encoding='utf-8') as json_file:
        json.dump(data, json_file, ensure_ascii=False, indent=4)

def remove_main_domain(url):
    parsed_url = urlparse(url)
    return parsed_url.path

def download_pdf(data):
    base_url = "http://www.cassation.tn/"
    output_folder = "./output"

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    if data['pdf_ar']:
        pdf_ar_url = base_url + data['pdf_ar']
        pdf_ar_path = remove_main_domain(data['pdf_ar'])
        pdf_ar_path = os.path.join(output_folder, pdf_ar_path.lstrip('/'))

        os.makedirs(os.path.dirname(pdf_ar_path), exist_ok=True)
        download_file(pdf_ar_url, pdf_ar_path)

def download_file(url, path):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }
    response = requests.get(url, verify=False, headers=headers)
    if response.status_code == 200:
        with open(path, 'wb') as file:
            file.write(response.content)

def process_cassation(dataC, id):
    try:
        print(dataC)
        links_num_parts = dataC['links_num'].split(':')
        numero = links_num_parts[1] if len(links_num_parts) > 1 else "Not found"
        
        links_date_parts = dataC['links_date'].split(':')
        date = links_date_parts[1] if len(links_date_parts) > 1 else "Not found"
        
        links_matiere_parts = dataC['links_matiere'].split(':')
        matier = links_matiere_parts[1] if len(links_matiere_parts) > 1 else "Not found"
        
        date = date.replace('.', '/')

        data = {
            'original_id': "",
            'ministry': "",
            'date_article': "",
            'year': "",
            'month': "",
            'day': "",
            'jort_year': "",
            'jort_num': "",
            'lang': "",
            'pagination_fr': "",
            'pagination_ar': "",
            'content': "",
            'key_word': [],
            'pdf_ar': "",
            'pdf_fr': "",
            'categorie': ""
        }
        data['original_id'] = id
        data['date_article'] = date
        data['categorie'] = matier
        data['content'] = dataC['links_sujet']
        data['pdf_ar'] = dataC['links_download_url'].replace('http://www.cassation.tn/', '')
        data['day'] = date.split('/')[0]
        data['month'] = date.split('/')[1]
        data['year'] = date.split('/')[2]
        data['lang'] = "ar"
        data['pagination_fr'] = None
        data['pagination_ar'] = None
        data['key_word'] = dataC['links_sujet'].split('-')
        data['ministry'] = "justice"
        data['jort_year'] = date.split('/')[2]
        data['jort_num'] = numero

        # Step 5: Save the data to a file
        save_json(data, 'cassation', id)
        download_pdf(data)
        log_message("Data saved to file." + str(id))
    except Exception as e:
        log_message(f"Error processing cassation data for id {id}: {str(e)}")

def read_json():
    with open('output.json', 'r', encoding='utf-8') as file:
        data = json.load(file)
    return data 

data = read_json()
# for each json object in the array
for i in range(len(data)):
    process_cassation(data[i], i)