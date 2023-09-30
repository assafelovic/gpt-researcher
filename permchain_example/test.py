# main
import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from permchain_example.researcher import Researcher
from permchain_example.search_actors.search_api import TavilySearchActor
from permchain_example.editor_actors.editor import EditorActor
from permchain_example.reviser_actors.reviser import ReviserActor
from permchain_example.search_actors.gpt_researcher import GPTResearcherActor
from permchain_example.writer_actors.writer import WriterActor
from permchain_example.research_team import ResearchTeam
from processing.text import md_to_pdf



if __name__ == '__main__':
    output_path = "./output"
    if not os.path.exists(output_path):
        # If the directory does not exist, create it
        os.makedirs(output_path)

    stocks = ["NVDA"]

    for stock in stocks[:1]:
        query = f"is the stock {stock} a good buy?"
        researcher = Researcher(GPTResearcherActor(), WriterActor())
        research_team = ResearchTeam(researcher, EditorActor(), ReviserActor())

        draft = research_team.run(query)
        with open(f"{output_path}/{stock}.md", "w") as f:
            f.write(draft)
        md_to_pdf(f"{output_path}/{stock}.md", f"{output_path}/{stock}.pdf")