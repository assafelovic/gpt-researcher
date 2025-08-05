from gllm_docproc.downloader.html.scraper.web_scraper_executor import WebScraperExecutor
from gllm_docproc.parser.html import HTMLFlatParser
from gllm_docproc.downloader.html import HTMLDownloader
import json
from gllm_docproc.loader.html import HTMLFlatLoader
from gllm_docproc.loader import PipelineLoader
from gllm_docproc.downloader.html.utils import clean_url



urls = "https://www.scrapethissite.com/pages/"


# scraper = WebScraperExecutor(
#             urls=urls
# )
# result = scraper.get_url_content_pairs()


# content = result[0][1].decode("utf-8") if isinstance(result[0][1], bytes) else result[0][1]

output_dir = 'downloader_htmldownloader/output/download'
down = HTMLDownloader()
down.download("https://www.scrapethissite.com/pages/",output_dir)

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







