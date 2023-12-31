from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

import os
import openai
import PyPDF2
import requests

from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

openai.organization = os.getenv("ORG_KEY")
openai.api_key = os.getenv("OPENAI_API_KEY")

def analyze_large_text(text):
    max_tokens = 4000  # Keep it less than 4097 to account for extra tokens in the prompt
    segments = [text[i:i + max_tokens] for i in range(0, len(text), max_tokens)]
    is_relevant = False

    for segment in segments:
        analysis_result = analyze_content_with_gpt4(segment)
        if analysis_result:  # If any segment is relevant, the whole text is marked as relevant
            is_relevant = True
            break

    return is_relevant

def analyze_content_with_gpt4(text):
    print(f"Sending segment to GPT: {text[:100]}...")  # Print first 100 characters for debug
    
    # Define the prompt, incorporating the text from the PDF
    prompt = f"Is this pdf from 2022? Text: {text}"

    # Query GPT-4
    response = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=[{"role": "system", "content": "You are a helpful assistant."}, {"role": "user", "content": f"Does the following text discuss biodiversity? Text: {text}"}])

    # Analyze the response
    # You might want to customize this part depending on how you've structured the prompt
    analysis_result = response.choices[0].message['content']

    # Define the logic to determine if the PDF is relevant
    # This might be as simple as checking if the response is 'yes' or 'no'
    is_relevant = analysis_result.lower() == 'yes'

    print(f"GPT-4 said: {analysis_result}")  # Print GPT-4 analysis for debug
    return is_relevant

def download_page(driver, url):
    driver.get(url)
    return BeautifulSoup(driver.page_source, 'html.parser')

def download_and_extract_pdf_text(url):
    session = requests.Session()
    retry = Retry(total=5, backoff_factor=0.1, status_forcelist=[500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)

    try: 
        response = session.get(url)
        print(f"PDF Response Status: {response.status_code}")  # Debug
        
        if response.status_code == 200:
            with open('temp.pdf', 'wb') as f:
                f.write(response.content)

            with open('temp.pdf', 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                text = ' '.join([page.extract_text() for page in reader.pages if page.extract_text().strip()])

            os.remove('temp.pdf')
            return text
        else:
            print(f"PDF download failed: {response.status_code}")
            return None
            
    except Exception as e:  # Broad exception to catch any issue
        print(f"Error reading PDF from {url}: {e}")
        return None

def download_pdfs(soup, base_url, download_dir):
    for link in soup.find_all('a'):
        url = link.get('href', '')
        if url.endswith('.pdf'):
            full_url = url if 'http' in url else base_url + url
            print(f"Full URL: {full_url}")  # Debug line
            
            # Check if URL is valid
            response = requests.head(full_url)
            if response.status_code != 200:
                print(f"PDF Response Status: {response.status_code}")
                print(f"PDF download failed: {response.status_code}")
                continue
            
            text_sample = download_and_extract_pdf_text(full_url)
            analysis_result = None  # Initialize to None
            
            if text_sample is not None:
                analysis_result = analyze_large_text(text_sample)
            
            if analysis_result:
                download_file(full_url, download_dir)
            else:
                print(f"Skipping {full_url} due to not meeting criteria.")


def download_file(url, download_dir):
    print(f"Downloading file from: {url}")
    response = requests.get(url, stream=True)

    if response.status_code == 200:
        filename = url.split('/')[-1]
        with open(os.path.join(download_dir, filename), 'wb') as out_file:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    out_file.write(chunk)
    else:
        print(f"Failed to download {url}. Status code: {response.status_code}")

def scrape_text(soup):
    text = soup.get_text()
    with open('scraped_text.txt', 'a', encoding='utf-8') as f:
        f.write(text)

# set up webdriver
webdriver_service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=webdriver_service)

# replace with the website you want to scrape from
base_url = 'https://www.worldwildlife.org/about/financials'

# replace with your desired download directory
download_dir = os.getenv('DIR_PATH')

soup = download_page(driver, base_url)
scrape_text(soup)
download_pdfs(soup, base_url, download_dir)

# clean up
driver.quit()
