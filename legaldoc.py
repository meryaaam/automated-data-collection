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



load_dotenv()

# Define the OpenSearch endpoint and index name
opensearch_url = os.getenv('OPENSEARCH_URL')
username = os.getenv('OSEARCH_USERNAME')
password = os.getenv('PASSWORD')

host = urlparse(opensearch_url).hostname 
port = urlparse(opensearch_url).port
auth=(username, password) 
ssl_verification = True  # Set to False if you want to disable SSL verification

client = OpenSearch(
hosts = [{'host': host, 'port': port}],
        http_compress = True, # enables gzip compression for request bodies
        http_auth = auth,
        use_ssl = ssl_verification,
        verify_certs = ssl_verification,
        ssl_assert_hostname = False,
        ssl_show_warn = False 
    )

# Define the index mapping
index_mapping = {
    "mappings": {
        "properties": { 
            "doc_id" : {"type": "keyword"},
            "original_id": {"type": "keyword"},
            "ministry": {"type": "keyword"},
            "date_article": {"type": "date", "format": "dd/MM/yyyy"},
            "published_at" : {"type": "date", "format": "dd/MM/yyyy"},
            "year": {"type": "keyword"},
            "month": {"type": "keyword"},
            "day": {"type": "keyword"},
            "jort_year": {"type": "keyword"},
            "jort_num": {"type": "keyword"},
            "lang": {"type": "keyword"},
            "pagination_fr": {"type": "text"},
            "pagination_ar": {"type": "text"},
            "content": {"type": "text"},
            "key_word": {"type": "keyword"},
            "pdf_ar": {"type": "keyword"},
            "pdf_fr": {"type": "keyword"},
            "categorie": {"type": "keyword"}
        }
    }
}

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


input=[]

def get_table_data(url):

    # Path to the JSON file
    json_file_path = './output/input.json'

    # Read the JSON file
    with open(json_file_path, 'r') as file:
        data = json.load(file)

    # Assuming the JSON file contains an array

    new_input=data
    # Fetch the HTML content from the URL
    response = requests.get(url)
    response.raise_for_status()  # Check if the request was successful

    # Parse the HTML content using BeautifulSoup
    soup = BeautifulSoup(response.text, 'html.parser')

    # Debug: Print the HTML content
    # print(soup.prettify())

    # Find the table with the class 'narrowandfocusonsearchbox'
    table = soup.find('table', class_='narrowandfocusonsearchbox')

    # Check if the table is found
    if table is None:
        print("Table with class 'narrowandfocusonsearchbox' not found.")
        return

    # Iterate through each 'tr' element in the table
    for tr in table.find_all('tr'):
        tds = tr.find_all('td')
        if len(tds) > 1:
            # Get the URL from the 'a' tag in the second 'td'
            a_tag = tds[1].find('a')
            if a_tag and 'href' in a_tag.attrs:
                url = a_tag['href']
                # Extract value between /collection/ and ?
                match = re.search(r'/collection/(.*?)(\?|$)', url)
                if match:
                    collection_value = match.group(1)

                    # Get the value from the 'small' tag in the second 'td'
                    small_tag = tds[1].find('small')
                    if small_tag:
                        small_value = small_tag.text
                        # Remove parentheses and numbers without commas
                        cleaned_small_value = small_value.replace('(', '').replace(')', '').replace(' ', '').replace(',', '')

                        # Search for the collection value in the input data

    return data
  
def create_index(index_name):
    try: 
        index_body = {
            'settings': {
                'index': {
                'number_of_shards': 4
                }
            }
        }
        exist = client.indices.exists(index_name) 

        if not exist:
            response = client.indices.create(index_name)
            print(f"Index {index_name} created") 
    except Exception as e:
        print(f"An error occurred: {e}")


def readPDF(pdfFile):
    full_text = ""
    try:
        if not os.path.exists(pdfFile):
            return full_text
            raise FileNotFoundError(f"The file {pdfFile} does not exist.")


        pdf_file = open(pdfFile, "rb")
        full_text = ""
        # Create a PDF reader object
        pdf_reader = PdfReader(pdf_file)
        for page_number in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_number]
            page_text = page.extract_text()
            full_text += page_text
            coded_pdf = full_text.find("Page") if full_text.find("Page") != -1 else (
                 full_text.find("page") if full_text.find("page") != -1 else (
                    full_text.find("ﺻﻔﺤــﺔ") if full_text.find("ﺻﻔﺤــﺔ") != -1 else (
                        full_text.find("صفحـة") if full_text.find("صفحـة") != -1 else (
                            full_text.find("صفحة") if full_text.find("صفحة") != -1 else 0
                        )
                    )
                )
            )        
        return full_text if coded_pdf != 0 else "" 

    except FileNotFoundError as e:
        print(f"Error: {e}")
        return full_text
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return full_text


def check_existance (index , original_id , jort_num , jort_year , lang):
    index_name = index  
    query = {
        "size": 1,   
        "query": {
            "bool": {
                "must": [
                    {"term": {"original_id": original_id}},   
                    {"term": {"jort_num": jort_num}},         
                    {"term": {"jort_year": jort_year}},       
                    {"term": {"lang": lang}}                 
                ]
            }
        }
    }
    
    try: 
        response = client.search( body = query,  index = index_name ) 
        if 'hits' in response and response['hits']['total']['value'] > 0:
            return response['hits']['hits'][0]['_id']
        else:
            return 0
    except Exception as e:
        print(f"An error occurred: {e}")
        return 0

def batch_process(data, batch_size):
    """
    Yields batches of data of a specified size.

    :param data: The collection to be batched.
    :param batch_size: The size of each batch.
    """
    for i in range(0, len(data), batch_size):
        yield data[i:i + batch_size]

def push_data(index_name,file_name):
    
    BATCH_SIZE = 250

    # Load data from JSON file
    with open("./output_json/"+file_name+'.json', 'r', encoding='utf-8') as file:
        data = json.load(file)

    batch_number = 1

    # Prepare bulk data
    for batch in batch_process(data, BATCH_SIZE):
        bulk_data = ''
        for record in batch:  
            old_id = check_existance(index_name , record['original_id'] , record['jort_num'] , record['jort_year'] , record['lang'])  
            id = record['doc_id']+"-"+record['original_id']
            if old_id != 0 : 
                if old_id == id :
                    bulk_data += json.dumps({"index": {"_index": index_name, "_id": id}}) + "\n"
                else :
                    bulk_data += json.dumps({"delete": {"_index": index_name, "_id": old_id}}) + "\n" 
                    bulk_data += json.dumps({"index": {"_index": index_name , "_id": id}}) + '\n'
            else: 
                bulk_data += json.dumps({"index": {"_index": index_name , "_id": id}}) + '\n'
                
            
            bulk_data += json.dumps(record) + '\n'

        try:    
            response = client.bulk(bulk_data) 
            print('documents added/updated in opsearch')
        except Exception as e:
            print(f"An unexpected error from opensearch occurred: {e}")
        
        print(f"Batch {batch_number} {'-' * 50}")
        batch_number += 1





def remove_main_domain(url):
    parsed_url = urlparse(url)
    return parsed_url.path

def get_folders(directory):
    """Get a list of folders in the given directory."""
    return [f for f in os.listdir(directory) if os.path.isdir(os.path.join(directory, f))]

def read_json_files(folder_path):
    """Read all JSON files in the given folder and return their contents as a list."""
    json_contents = []
    for file_name in os.listdir(folder_path):
        if file_name.endswith('.json'):
            file_path = os.path.join(folder_path, file_name)
            with open(file_path, 'r', encoding='utf-8') as json_file:
                json_contents.append(json.load(json_file))
    return json_contents

def create_json_for_folders(directory):
    """Create a JSON file for each folder containing an array of the contents of each JSON file in the folder."""
    folders = get_folders(directory)
    for folder in folders:
        folder_path = os.path.join(directory, folder)
        json_contents = read_json_files(folder_path)
        json_file_path = os.path.join(directory, f"{folder}.json")
        with open(json_file_path, 'w', encoding='utf-8') as json_file:
            json.dump(json_contents, json_file, ensure_ascii=False, indent=4)

def create_collection(directory):
    create_json_for_folders(directory)


def download_pdf(data):
    base_url = "https://www.pist.tn"
    output_folder = "./output"

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    if data.get('pdf_ar'):
        if data['pdf_ar'].startswith('http'):
            pdf_ar_url = data['pdf_ar']
            pdf_ar_path = remove_main_domain(data['pdf_ar'])
            pdf_ar_path = os.path.join(output_folder, pdf_ar_path.lstrip('/'))
        else:
            pdf_ar_url = base_url + data['pdf_ar']
            pdf_ar_path = os.path.join(
                output_folder, data['pdf_ar'].lstrip('/'))
        os.makedirs(os.path.dirname(pdf_ar_path), exist_ok=True)
        download_file(pdf_ar_url, pdf_ar_path)

    if data.get('pdf_fr'):
        if data['pdf_fr'].startswith('http'):
            pdf_fr_url = data['pdf_fr']
            pdf_fr_path = remove_main_domain(data['pdf_fr'])
            pdf_fr_path = os.path.join(output_folder, pdf_fr_path.lstrip('/'))
        else:
            pdf_fr_url = base_url + data['pdf_fr']
            pdf_fr_path = os.path.join(
                output_folder, data['pdf_fr'].lstrip('/'))
        os.makedirs(os.path.dirname(pdf_fr_path), exist_ok=True)
        download_file(pdf_fr_url, pdf_fr_path)


def download_file(url, path):
    response = requests.get(url, verify=False)
    if response.status_code == 200:
        with open(path, 'wb') as file:
            file.write(response.content)
    else:
        logging.info(f"Failed to download {url}")


def fetch_xml(url):
    try:
        response = requests.get(url, verify=False)
        response.raise_for_status()  # Raise an error for bad status codes
        return response.content
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching XML from URL: {url} - {e}")
        raise


def save_json(data, category, original_id,original_data):
    # Create the directory if it doesn't exist
    directory = os.path.join('output_json', original_data['index'])
    os.makedirs(directory, exist_ok=True)

    # Define the file path
    file_path = os.path.join(directory, f"{original_id}.json")

    # Save the JSON data to the file
    with open(file_path, 'w', encoding='utf-8') as json_file:
        json.dump(data, json_file, ensure_ascii=False, indent=4)


def parse_xml(xml_content):
    ns = {'marc': 'http://www.loc.gov/MARC21/slim'}
    root = ET.fromstring(xml_content)
    records = root.findall('marc:record', ns)
    return records


def process_record(record, ns , index):
    data = {
        'doc_id' : "" ,
        'original_id': "",
        'ministry': "",
        'date_article': "",
        'published_at' : "",
        'year': "",
        'month': "",
        'day': "",
        'jort_year': "",
        'jort_num': "",
        'lang': "",
        'pagination_fr': "",
        'pagination_ar': "",
        'content': "",
        'pdf_content' :"",
        'pdf_content_ar' :"",
        'key_word': [],
        'pdf_ar': "",
        'pdf_fr': "",
        'categorie': ""
    }

    data['original_id'] = record.find(
        'marc:controlfield[@tag="001"]', ns).text or ""
 
    datafield_110 = record.find(
        'marc:datafield[@tag="110"]/marc:subfield[@code="a"]', ns)
    data['ministry'] = datafield_110.text if datafield_110 is not None else ""

    data['published_at'] = datetime.now().strftime("%d/%m/%Y")
    datafield_946 = record.find('marc:datafield[@tag="946"]', ns)
    if datafield_946 is not None:
        
        date_article = datafield_946.find('marc:subfield[@code="z"]', ns)
        
        data['date_article'] = date_article.text if date_article is not None else datafield_946.find('marc:subfield[@code="s"]', ns).text

        year = datafield_946.find('marc:subfield[@code="y"]', ns)
        data['year'] = year.text if year is not None else datafield_946.find('marc:subfield[@code="r"]', ns).text

        month = datafield_946.find('marc:subfield[@code="u"]', ns)
        data['month'] = month.text if month is not None else datafield_946.find('marc:subfield[@code="q"]', ns).text

        day = datafield_946.find('marc:subfield[@code="t"]', ns)
        data['day'] = day.text if day is not None else datafield_946.find('marc:subfield[@code="p"]', ns).text
    
    datafield_093 = record.find('marc:datafield[@tag="093"]', ns)
     
    if datafield_093 is not None:
        jort_year = datafield_093.find('marc:subfield[@code="d"]', ns)
        data['jort_year'] = jort_year.text if jort_year is not None else data['year']

        jort_num = datafield_093.find('marc:subfield[@code="j"]', ns)
        data['jort_num'] = jort_num.text if jort_num is not None else ""

    datafield_040 = record.find(
        'marc:datafield[@tag="040"]/marc:subfield[@code="b"]', ns)
    data['lang'] = datafield_040.text if datafield_040 is not None else ""

    datafield_300 = record.find(
        'marc:datafield[@tag="300"]/marc:subfield[@code="a"]', ns)
    data['pagination_fr'] = datafield_300.text if datafield_300 is not None else ""

    datafield_534 = record.find(
        'marc:datafield[@tag="534"]/marc:subfield[@code="3"]', ns)
    data['pagination_ar'] = datafield_534.text if datafield_534 is not None else ""

    datafield_245 = record.findall(
        'marc:datafield[@tag="245"]/marc:subfield', ns)
    data['content'] = ' '.join(
        [subfield.text for subfield in datafield_245 if subfield.text is not None])

    data['key_word'] = [subfield.text for subfield in record.findall(
        'marc:datafield[@tag="653"]/marc:subfield[@code="a"]', ns) if subfield.text is not None]

    datafield_856 = record.findall(
        'marc:datafield[@tag="856"]/marc:subfield[@code="u"]', ns)
    if len(datafield_856) > 0:
        data['pdf_ar'] = datafield_856[0].text or ""
    if len(datafield_856) > 1:
        data['pdf_fr'] = datafield_856[1].text or ""
    datafield_245 = record.find('marc:datafield[@tag="690"]', ns)
    if datafield_245 is not None:
        data['categorie'] = datafield_245.find(
            'marc:subfield[@code="a"]', ns).text or ""

    data['pdf_content'] = readPDF('./output'+data['pdf_fr']) if data['pdf_fr'] else '' 
    data['pdf_content_ar'] = readPDF('./output'+data['pdf_ar']) if data['pdf_ar'] else '' 
    data['doc_id'] = index+'-'+ data['date_article'].replace( '/', '-')
    return data

def process_group(url,original_data):
    print(url)
    xml_content = fetch_xml(url)
    records = parse_xml(xml_content)
    ns = {'marc': 'http://www.loc.gov/MARC21/slim'}
    index = original_data['index']
    for record in records:
        data = process_record(record, ns,index)
        id = data['original_id']
        file = "output_json/"+index+"/"+id+".json"
         
        if not os.path.exists(file): 
            print(f"Record {data['original_id']}: {data['categorie']} processed")
            save_json(data, data['categorie'], data['original_id'],original_data)
            logging.info(f"Record {data['original_id']}: {data['categorie']} saved")
            download_pdf(data)
        else:
              print(f"Record {data['original_id']}: {data['categorie']} already exist in {file}")

def process_download_items(key,total_items,original_data):
    if total_items <500 :
        batch_size = total_items
    else:
        batch_size = 500
    num_batches = (total_items + batch_size - 1) // batch_size  # Calculate the number of batches

    for i in range(num_batches):
        start_item = i * batch_size + 1
        print(f"Processing batch {i+1}/{num_batches}")
        url = f"https://www.pist.tn/search?cc={key}&ln=fr&rg={batch_size}&jrec={start_item}&of=xm"
        process_group(url,original_data)  # Call your processing function with the generated URL

if __name__ == "__main__":
    input=get_table_data('https://www.pist.tn/collection/JORT?ln=fr')
    print(input)
    for item in input:
         
        if int(item['new_total'])>int(item['total']):
            print("Downloading new items")
            print(item['key'])
            process_download_items(item['key'],int(item['new_total'])-int(item['total']),item)  # Call your processing function with the generated URL
    create_collection("./output_json")  # Create the collection JSON file
    for item in input:
        
        create_index('legaldoc_'+item['index'])
        push_data('legaldoc_'+item['index'],item['index'])
    
    for item in input:
        item['total'] = item['new_total']

    # Save new_input to ./output/input.json
    with open('./output/input.json', 'w', encoding='utf-8') as json_file:
        json.dump(input, json_file, ensure_ascii=False, indent=4)
