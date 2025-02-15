import requests
from bs4 import BeautifulSoup
import json
import requests
import os
from urllib.parse import urlparse
def save_json(data, category, original_id):
    # Create the directory if it doesn't exist
    directory = os.path.join('output_json', category)
    os.makedirs(directory, exist_ok=True)

    # Define the file path
    file_path = os.path.join(directory, f"{original_id}.json")

    # Save the JSON data to the file
    with open(file_path, 'w', encoding='utf-8') as json_file:
        json.dump(data, json_file, ensure_ascii=False, indent=4)

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
        pdf_ar_url = base_url+data['pdf_ar']
        pdf_ar_path = remove_main_domain(data['pdf_ar'])
        pdf_ar_path = os.path.join(output_folder, pdf_ar_path.lstrip('/'))

        os.makedirs(os.path.dirname(pdf_ar_path), exist_ok=True)
        download_file(pdf_ar_url, pdf_ar_path)



def download_file(url, path):
    print("Downloading file from:", url)
    print("Saving to:", path)
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }
    response = requests.get(url, verify=False ,headers=headers)
    print(response.status_code)
    if response.status_code == 200:
        with open(path, 'wb') as file:
            file.write(response.content)

def process_cassation(id):
    # Step 1: Get HTML content from URL
    url = 'http://www.cassation.tn/fr/%D9%81%D9%82%D9%87-%D8%A7%D9%84%D9%82%D8%B6%D8%A7%D8%A1/?tx_uploadexample_piexample%5Bexample%5D=50&tx_uploadexample_piexample%5Baction%5D=show&tx_uploadexample_piexample%5Bcontroller%5D=Example'  # Replace with your URL

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }

    response = requests.get(url, headers=headers)
    html_content = response.text
    
    # Step 2: Parse HTML content
    soup = BeautifulSoup(html_content, 'html.parser')

    # Step 3: Extract the content of the div with class 'tx-upload-example'
    content_div = soup.find('div', class_='tx-upload-example')

    print(content_div)
    # Debugging: Print the content of the div
    # Step 4: Extract date, matier, and numero
    if content_div:
        # Debugging: Print all h4 tags
        title=content_div.find('h3').get_text(strip=True)
        for h4 in content_div.find_all('h4'):
            print("Found h4 tag:", h4.get_text(strip=True))
        
        numero_tag = content_div.find_all('h4')[0]
        date_tag = content_div.find_all('h4')[1]
        matier_tag = content_div.find_all('h4')[2]

        if numero_tag is None:
            print("Numero tag not found")
        if date_tag is None:
            print("Date tag not found")
        if matier_tag is None:
            print("Matier tag not found")
        
        numero = numero_tag.get_text(strip=True).split(':')[1] if numero_tag else "Not found"
        date = date_tag.get_text(strip=True).split(':')[1] if date_tag else "Not found"
        matier = matier_tag.get_text(strip=True).split(':')[1] if matier_tag else "Not found"
        date = date.replace('.', '/')
        print("Numero:", numero)
        print("Date:", date)
        print("Matier:", matier)
        print("Title:", title)
        
        # Extract the link from the a tag within the h4 tag with class 'buttom'
        h4_tag = content_div.find('h4', class_='buttom')
        if h4_tag:
            a_tag = h4_tag.find('a')
            if a_tag and 'href' in a_tag.attrs:
                link = a_tag['href']
                print("Link found:", link)
            else:
                print("No a tag with href found in h4 tag.")
        else:
            print("No h4 tag with class 'buttom' found in the div.")
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
        data['content'] = title
        data['pdf_ar'] = link
        data['day'] = date.split('/')[0]
        data['month'] = date.split('/')[1]
        data['year'] = date.split('/')[2]
        data['lang'] = "fre"
        data['pagination_fr'] = None
        data['pagination_ar'] = None
        data['key_word'] = title.split('-')
        data['ministry'] = "justice"
        data['jort_year'] = None
        data['jort_num'] = None

        #step 5: Save the data to a file
        save_json(data, 'cassation', id)
        download_pdf(data)

    else:
        print("No div with class 'tx-upload-example' found.")

#for from 5409 down to 10
for i in range(10000, 10, -1):
    process_cassation(i)
       