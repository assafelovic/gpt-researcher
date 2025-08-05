from gllm_docproc.downloader.html.firecrawl_downloader import HTMLFirecrawlDownloader
from gllm_docproc.downloader.html.scraper.web_scraper_executor import WebScraperExecutor
from gllm_docproc.parser.html import HTMLFlatParser
import json
from gllm_docproc.loader.html import HTMLFlatLoader
from gllm_docproc.loader import PipelineLoader
from gllm_docproc.downloader.html.utils import clean_url
from dotenv import load_dotenv
import os
load_dotenv()

FirecrawlAPIKEY = os.getenv("FIRECRAWL_API_KEY")

urls = "https://www.scrapethissite.com/pages/"
output_dir = 'downloader_firecrawldownloader/output/download'
downloader = HTMLFirecrawlDownloader(api_key=FirecrawlAPIKEY)
downloader.download(urls,output_dir)

downloaded_html_json_path = output_dir + "/" + clean_url(urls) + ".json"
with open(downloaded_html_json_path, "r") as f:
    downloaded_html_json = json.load(f)
    loader_source = downloaded_html_json.get("content")


pipe = PipelineLoader()
pipe.add_loader(HTMLFlatLoader())
loaded_elements = pipe.load(loader_source)
print("Successfully loaded HTML with total %d elements", len(loaded_elements))
print(type(loaded_elements))

parser = HTMLFlatParser()
res = parser.parse(loaded_elements)
print(res)