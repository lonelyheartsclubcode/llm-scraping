# Web Scraper Project

This project is a simple web scraper built in Python. It is designed to scrape webpages for PDF documents, which it then downloads for further use.

## Setup

1. Make sure Python 3 and pip are installed on your system.

2. Clone this repository or download the project files.

3. Navigate to the project directory and install the necessary Python libraries with pip:
    ```
    pip3 install -r requirements.txt
    ```

## Usage

To use the web scraper, modify the `scraper.py` file with the URL(s) of the site(s) you wish to scrape. Then, run the script from the terminal with:

python3 scraper.py


The script will download all found PDFs and save them in the `pdfs` directory.

Please respect the terms of service of the websites you are scraping and avoid overloading servers with too many requests.
