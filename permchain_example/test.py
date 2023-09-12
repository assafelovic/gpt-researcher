# main
import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from permchain_example.researcher import Researcher
from permchain_example.search_actors.search_api import TavilySearchActor
from permchain_example.search_actors.gpt_researcher import GPTResearcherActor
from permchain_example.writer_actors.openai import OpenAIWriterActor
from processing.text import md_to_pdf



if __name__ == '__main__':
    output_path = "./permchain_example/output"
    if not os.path.exists(output_path):
        # If the directory does not exist, create it
        os.makedirs(output_path)

    def md2pdf(md_file, pdf_file):
        md_to_pdf(md_file, pdf_file)

    stocks = ["MSFT"]

    for stock in stocks[:1]:
        researcher = Researcher(GPTResearcherActor(), OpenAIWriterActor())
        research = researcher.run(stock)
        with open(f"{output_path}/{stock}.md", "w") as f:
            f.write(research)
        md2pdf(f"{output_path}/{stock}.md", f"{output_path}/{stock}.pdf")


