import asyncio

from gpt_researcher import GPTResearcher

from langchain_community.vectorstores import InMemoryVectorStore
from langchain_openai import OpenAIEmbeddings

from dotenv import load_dotenv

load_dotenv()

async def main():
    vector_store = InMemoryVectorStore(embedding=OpenAIEmbeddings())

    query = "Which one is the best LLM"

    # Create an instance of GPTResearcher
    researcher = GPTResearcher(
        query=query,
        report_type="research_report",
        report_source="web",
        vector_store=vector_store, 
    )

    # Conduct research and write the report
    await researcher.conduct_research()

    # Check if the vector_store contains information from the sources
    related_contexts = await vector_store.asimilarity_search("GPT-4", k=5)
    print(related_contexts)
    print(len(related_contexts))


asyncio.run(main())