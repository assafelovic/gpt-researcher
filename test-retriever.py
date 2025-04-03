import asyncio
from dotenv import load_dotenv
from gpt_researcher.config.config import Config
from gpt_researcher.actions.retriever import get_retrievers
from gpt_researcher.skills.researcher import ResearchConductor
import pprint
# Load environment variables from .env file
load_dotenv()

async def test_scrape_data_by_query():
    # Initialize the Config object
    config = Config()

    # Retrieve the retrievers based on the current configuration
    retrievers = get_retrievers({}, config)
    print("Retrievers:", retrievers)

    # Create a mock researcher object with necessary attributes
    class MockResearcher:
        def init(self):
            self.retrievers = retrievers
            self.cfg = config
            self.verbose = True
            self.websocket = None
            self.scraper_manager = None  # Mock or implement scraper manager
            self.vector_store = None  # Mock or implement vector store

    researcher = MockResearcher()
    research_conductor = ResearchConductor(researcher)
    # print('research_conductor',dir(research_conductor))
    # print('MockResearcher',dir(researcher))
    # Define a sub-query to test
    sub_query = "How to deploy a nx monorepo on GCP?"
    # sub_query = "I have a nx monorepo (which contains next js project app + one-off-scripts (node js scripts)), I have build a docker image for this monorepo and copied the nx monorepo to the container, and in that we have used npm run build ( a custom script defined in root level package.json) to run my next js app which is working fine. They are using cloud build to deploy the app and cloud run to run the application. Now I want to use this infrastrucutre to run cron like jobs for my one-off-scripts folder which contains node js scripts which run periodically they use the same env variables used for my next js app also, right now this all is being executed in github actions, but I don’t want to use that because of security reasons, use only GCP for doing this."

    # Iterate through all retrievers
    for retriever_class in retrievers:
        # Instantiate the retriever with the sub-query
        retriever = retriever_class(sub_query)

        # Perform the search using the current retriever
        search_results = await asyncio.to_thread(
            retriever.search, max_results=3
        )

        print("\033[35mSearch results:\033[0m")
        pprint.pprint(search_results, indent=4, width=80)

if __name__ == "__main__":
    asyncio.run(test_scrape_data_by_query())