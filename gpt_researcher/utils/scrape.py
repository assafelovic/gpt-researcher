import requests
from bs4 import BeautifulSoup

class Scrape:
    def __init__(self, url):
        self.url = url
        self.soup = self.get_soup()