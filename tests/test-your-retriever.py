import os
from dotenv import load_dotenv
from gpt_researcher.config.config import Config
from gpt_researcher.actions.retriever import get_retrievers

# Load environment variables from .env file
load_dotenv()

def test_retriever_configuration():
    # Initialize the Config object
    config = Config()

    # Retrieve the retrievers based on the current configuration
    retrievers = get_retrievers({}, config)

    # Print the retriever classes
    print("Configured Retrievers:")
    for retriever in retrievers:
        print(retriever.__name__)

if __name__ == "__main__":
    test_retriever_configuration()