# Vector Stores

The GPT Researcher package allows you to integrate with existing langchain vector stores that have been populated.
For a complete list of supported langchain vector stores, please refer to this [link](https://python.langchain.com/v0.2/docs/integrations/vectorstores/).

You can create a set of embeddings and langchain documents and store them in any supported vector store of your choosing.
GPT-Researcher will work with any langchain vector store that implements the `asimilarity_search` method.

**If you want to use the existing knowledge in your vector store, make sure to set `report_source="langchain_vectorstore"`. Any other settings will add additional information from scraped data and might contaminate your vectordb (See _How to add scraped data to your vector store_ for more context)**

## Faiss
```python
from gpt_researcher import GPTResearcher

from langchain_text_splitters import CharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

# exerpt taken from - https://paulgraham.com/wealth.html
essay = """
May 2004

(This essay was originally published in Hackers & Painters.)

If you wanted to get rich, how would you do it? I think your best bet would be to start or join a startup.
That's been a reliable way to get rich for hundreds of years. The word "startup" dates from the 1960s,
but what happens in one is very similar to the venture-backed trading voyages of the Middle Ages.

Startups usually involve technology, so much so that the phrase "high-tech startup" is almost redundant.
A startup is a small company that takes on a hard technical problem.

Lots of people get rich knowing nothing more than that. You don't have to know physics to be a good pitcher.
But I think it could give you an edge to understand the underlying principles. Why do startups have to be small?
Will a startup inevitably stop being a startup as it grows larger?
And why do they so often work on developing new technology? Why are there so many startups selling new drugs or computer software,
and none selling corn oil or laundry detergent?


The Proposition

Economically, you can think of a startup as a way to compress your whole working life into a few years.
Instead of working at a low intensity for forty years, you work as hard as you possibly can for four.
This pays especially well in technology, where you earn a premium for working fast.

Here is a brief sketch of the economic proposition. If you're a good hacker in your mid twenties,
you can get a job paying about $80,000 per year. So on average such a hacker must be able to do at
least $80,000 worth of work per year for the company just to break even. You could probably work twice
as many hours as a corporate employee, and if you focus you can probably get three times as much done in an hour.[1]
You should get another multiple of two, at least, by eliminating the drag of the pointy-haired middle manager who
would be your boss in a big company. Then there is one more multiple: how much smarter are you than your job
description expects you to be? Suppose another multiple of three. Combine all these multipliers,
and I'm claiming you could be 36 times more productive than you're expected to be in a random corporate job.[2]
If a fairly good hacker is worth $80,000 a year at a big company, then a smart hacker working very hard without 
any corporate bullshit to slow him down should be able to do work worth about $3 million a year.
...
...
...
"""

document = [Document(page_content=essay)]
text_splitter = CharacterTextSplitter(chunk_size=200, chunk_overlap=30, separator="\n")
docs = text_splitter.split_documents(documents=document)

vector_store = FAISS.from_documents(documents, OpenAIEmbeddings())

query = """
    Summarize the essay into 3 or 4 succinct sections.
    Make sure to include key points regarding wealth creation.

    Include some recommendations for entrepreneurs in the conclusion.
"""


# Create an instance of GPTResearcher
researcher = GPTResearcher(
    query=query,
    report_type="research_report",
    report_source="langchain_vectorstore",
    vector_store=vector_store,
)

# Conduct research and write the report
await researcher.conduct_research()
report = await researcher.write_report()
```


## PGVector
```python
from gpt_researcher import GPTResearcher
from langchain_postgres.vectorstores import PGVector
from langchain_openai import OpenAIEmbeddings

CONNECTION_STRING = 'postgresql://someuser:somepass@localhost:5432/somedatabase'


# assuming the vector store exists and contains the relevent documents
# also assuming embeddings have been or will be generated
vector_store = PGVector.from_existing_index(
    use_jsonb=True,
    embedding=OpenAIEmbeddings(),
    collection_name='some collection name',
    connection=CONNECTION_STRING,
    async_mode=True,
)

query = """
    Create a short report about apples.
    Include a section about which apples are considered best
    during each season.
"""

# Create an instance of GPTResearcher
researcher = GPTResearcher(
    query=query,
    report_type="research_report",
    report_source="langchain_vectorstore",
    vector_store=vector_store, 
)

# Conduct research and write the report
await researcher.conduct_research()
report = await researcher.write_report()
```
## Adding Scraped Data to your vector store

In some cases in which you want to store the scraped data and documents into your own vector store for future usages, GPT-Researcher also allows you to do so seamlessly just by inputting your vector store (make sure to set `report_source` value to something other than `langchain_vectorstore`)

```python
from gpt_researcher import GPTResearcher

from langchain_community.vectorstores import InMemoryVectorStore
from langchain_openai import OpenAIEmbeddings

vector_store = InMemoryVectorStore(embedding=OpenAIEmbeddings())

query = "The best LLM"

# Create an instance of GPTResearcher
researcher = GPTResearcher(
    query=query,
    report_type="research_report",
    report_source="web",
    vector_store=vector_store, 
)

# Conduct research, the context will be chunked and stored in the vector_store
await researcher.conduct_research()

# Query the 5 most relevant context in our vector store
related_contexts = await vector_store.asimilarity_search("GPT-4", k = 5) 
print(related_contexts)
print(len(related_contexts)) #Should be 5 
```
