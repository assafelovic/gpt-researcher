# Data Ingestion

When you're dealing with a large amount of context data, you may want to start meditating upon a standalone process for data ingestion.

Some signs that the system is telling you to move to a custom data ingestion process:

- Your embedding model is hitting API rate limits
- Your Langchain VectorStore's underlying database needs rate limiting
- You sense you need to add custom pacing/throttling logic in your Python code

As mentioned in our [YouTube Tutorial Series](https://www.youtube.com/watch?v=yRuduRCblbg), GPTR is using [Langchain Documents](https://python.langchain.com/api_reference/core/documents/langchain_core.documents.base.Document.html) and [Langchain VectorStores](https://python.langchain.com/v0.1/docs/modules/data_connection/vectorstores/) under the hood.

These are 2 beautiful abstractions that make the GPTR architecture highly configurable.

The current research flow, whether you're generating reports on web or local documents, is:

```bash
Step 1: transform your content (web results or local documents) into Langchain Documents
```

```bash
Step 2: Insert your Langchain Documents into a Langchain VectorStore
```

```bash
Step 3: Pass your Langchain Vectorstore into your GPTR report ([more on that here](https://docs.gptr.dev/docs/gpt-researcher/context/vector-stores) and below)
```

Code samples below:

Assuming your .env variables are like so:

```bash
OPENAI_API_KEY={Your OpenAI API Key here}
TAVILY_API_KEY={Your Tavily API Key here}
PGVECTOR_CONNECTION_STRING=postgresql://username:password...
```

Below is a custom data ingestion process that you can use to ingest your data into a Langchain VectorStore. See a [full working example here](https://github.com/assafelovic/gpt-researcher/pull/819#issue-2501632831).
In this example, we're using a Postgres VectorStore to embed data of a Github Branch, but you can use [any supported Langchain VectorStore](https://python.langchain.com/v0.2/docs/integrations/vectorstores/).

Note that when you create the Langchain Documents, you should include as metadata the `source` and `title` fields in order for GPTR to leverage your Documents seamlessly. In the example below, we're splitting the documents list into chunks of 100 & then inserting 1 chunk at a time into the vector store.

### Step 1: Transform your content into Langchain Documents

```python
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

async def transform_to_langchain_docs(self, directory_structure):
    documents = []
    splitter = RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=30)
    run_timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')

    for file_name in directory_structure:
        if not file_name.endswith('/'):
            try:
                content = self.repo.get_contents(file_name, ref=self.branch_name)
                try:
                    decoded_content = base64.b64decode(content.content).decode()
                except Exception as e:
                    print(f"Error decoding content: {e}")
                    print("the problematic file_name is", file_name)
                    continue
                print("file_name", file_name)
                print("content", decoded_content)

                # Split each document into smaller chunks
                chunks = splitter.split_text(decoded_content)

                # Extract metadata for each chunk
                for index, chunk in enumerate(chunks):
                    metadata = {
                        "id": f"{run_timestamp}_{uuid4()}",  # Generate a unique UUID for each document
                        "source": file_name,
                        "title": file_name,
                        "extension": os.path.splitext(file_name)[1],
                        "file_path": file_name
                    }
                    document = Document(
                        page_content=chunk,
                        metadata=metadata
                    )
                    documents.append(document)

            except Exception as e:
                print(f"Error saving to vector store: {e}")
                return None

    await save_to_vector_store(documents)
```

### Step 2: Insert your Langchain Documents into a Langchain VectorStore

```python
from langchain_postgres import PGVector
from langchain_postgres.vectorstores import PGVector
from sqlalchemy.ext.asyncio import create_async_engine

from langchain_community.embeddings import OpenAIEmbeddings

async def save_to_vector_store(self, documents):
    # The documents are already Document objects, so we don't need to convert them
    embeddings = OpenAIEmbeddings()
    # self.vector_store = FAISS.from_documents(documents, embeddings)
    pgvector_connection_string = os.environ["PGVECTOR_CONNECTION_STRING"]

    collection_name = "my_docs"

    vector_store = PGVector(
        embeddings=embeddings,
        collection_name=collection_name,
        connection=pgvector_connection_string,
        use_jsonb=True
    )

    # for faiss
    # self.vector_store = vector_store.add_documents(documents, ids=[doc.metadata["id"] for doc in documents])

    # Split the documents list into chunks of 100
    for i in range(0, len(documents), 100):
        chunk = documents[i:i+100]
        # Insert the chunk into the vector store
        vector_store.add_documents(chunk, ids=[doc.metadata["id"] for doc in chunk])
```

### Step 3: Pass your Langchain Vectorstore into your GPTR report

```python
async_connection_string = pgvector_connection_string.replace("postgresql://", "postgresql+psycopg://")

# Initialize the async engine with the psycopg3 driver
async_engine = create_async_engine(
    async_connection_string,
    echo=True
)

async_vector_store = PGVector(
    embeddings=embeddings,
    collection_name=collection_name,
    connection=async_engine,
    use_jsonb=True
)


researcher = GPTResearcher(
    query=query,
    report_type="research_report",
    report_source="langchain_vectorstore",
    vector_store=async_vector_store,
)
await researcher.conduct_research()
report = await researcher.write_report()
```   