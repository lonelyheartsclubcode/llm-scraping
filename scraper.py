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

openai.organization = os.getenv("ORG_KEY")
openai.api_key = os.getenv("OPENAI_API_KEY")

def analyze_content_with_gpt4(text):
    # Define the prompt, incorporating the text from the PDF
    prompt = f"Does the following text discuss the topic of interest? Text: {text}"

    # Query GPT-4
    response = openai.Completion.create(model="gpt-4.0-turbo", prompt=prompt)

    # Analyze the response
    # You might want to customize this part depending on how you've structured the prompt
    analysis_result = response.choices[0].text

    # Define the logic to determine if the PDF is relevant
    # This might be as simple as checking if the response is 'yes' or 'no'
    is_relevant = analysis_result.lower() == 'yes'

    return is_relevant

def download_page(driver, url):
    driver.get(url)
    return BeautifulSoup(driver.page_source, 'html.parser')

def download_and_extract_pdf_text(url):
    response = requests.get(url)
    with open('temp.pdf', 'wb') as f:
        f.write(response.content)
    
    with open('temp.pdf', 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        text = ' '.join([page.extract_text() for page in reader.pages])
    
    os.remove('temp.pdf')
    return text

def download_pdfs(soup, base_url, download_dir):
    for link in soup.find_all('a'):
        url = link.get('href', '')
        if url.endswith('.pdf'):
            full_url = base_url + url
            text_sample = download_and_extract_pdf_text(full_url)
            analysis_result = analyze_content_with_gpt4(text_sample)
            if analysis_result:
                download_file(full_url, download_dir)


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
base_url = 'https://www.chevron.com/annual-report'

# replace with your desired download directory
download_dir = '/Users/mikaadlin/web_scraper_project/downloads'

soup = download_page(driver, base_url)
scrape_text(soup)
download_pdfs(soup, base_url, download_dir)

# clean up
driver.quit()
