# Testing your Retriever

To test your retriever, you can use the following code snippet. The script will search for a sub-query and display the search results.

```python
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
    sub_query = "design patterns for autonomous ai agents"

    # Iterate through all retrievers
    for retriever_class in retrievers:
        # Instantiate the retriever with the sub-query
        retriever = retriever_class(sub_query)

        # Perform the search using the current retriever
        search_results = await asyncio.to_thread(
            retriever.search, max_results=10
        )

        print("\033[35mSearch results:\033[0m")
        pprint.pprint(search_results, indent=4, width=80)

if __name__ == "__main__":
    asyncio.run(test_scrape_data_by_query())
```

The output of the search results will include the title, body, and href of each search result. For example:
    
```json
[{   
    "body": "Jun 5, 2024 ... Three AI Design Patterns of Autonomous "
                "Agents. Overview of the Three Patterns. Three notable AI "
                "design patterns for autonomous agents include:.",
    "href": "https://accredianpublication.medium.com/building-smarter-systems-the-role-of-agentic-design-patterns-in-genai-13617492f5df",
    "title": "Building Smarter Systems: The Role of Agentic Design "
                "Patterns in ..."},
    ...]
```