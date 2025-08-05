from gllm_docproc.downloader.html.scraper.web_scraper_executor import WebScraperExecutor
from ..utils import clean_soup, get_text_from_soup, get_relevant_images, extract_title
from bs4 import BeautifulSoup

class WebScraperExecutorWrapper:
    
    def __init__(self, url,session=None):
        self.url = url
        self.session = session

    def scrape(self):
        scraper = WebScraperExecutor(
            urls=[self.url],
        )
        result = scraper.get_url_content_pairs()
        try:
            '''
            result is a list

            the first element is url (string)
            the second element is HTML Content as bytes
            '''
            content = result[0][1]
            soup = BeautifulSoup(
                content, 'lxml', from_encoding=None
            )
            cleaned_soup = clean_soup(soup)
            extracted_content = get_text_from_soup(cleaned_soup)
            images = get_relevant_images(cleaned_soup,self.url)
            title = extract_title(cleaned_soup)
            return extracted_content, images, title
        
        except Exception as e:
            print("Error! : " + str(e))
            return "", [], ""
