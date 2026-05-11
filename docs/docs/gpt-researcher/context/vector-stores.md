# Vector Stores

Das GPT-Researcher-Paket lässt sich mit vorhandenen LangChain-Vector-Stores verbinden, die bereits befüllt wurden.
Eine vollständige Liste unterstützter Vector Stores findest du in der [LangChain-Dokumentation](https://python.langchain.com/v0.2/docs/integrations/vectorstores/).

Du kannst Embeddings und LangChain-Dokumente erzeugen und in jeden unterstützten Vector Store schreiben.
GPT Researcher arbeitet mit jedem LangChain-Vector-Store, der die Methode `asimilarity_search` implementiert.

**Wenn du das vorhandene Wissen in deinem Vector Store nutzen willst, setze `report_source="langchain_vectorstore"`. Andere Einstellungen können zusätzliche Webdaten hinzufügen und deinen Vector Store vermischen.**

## Faiss

```python
from gpt_researcher import GPTResearcher
from langchain_text_splitters import CharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

# Beispieltext aus einem Paul-Graham-Essay
essay = """
May 2004

(This essay was originally published in Hackers & Painters.)

If you wanted to get rich, how would you do it? I think your best bet would be to start or join a startup.
...
"""

document = [Document(page_content=essay)]
text_splitter = CharacterTextSplitter(chunk_size=200, chunk_overlap=30, separator="\n")
docs = text_splitter.split_documents(documents=document)

vector_store = FAISS.from_documents(documents, OpenAIEmbeddings())

query = """
    Fasse den Essay in 3 oder 4 knappen Abschnitten zusammen.
    Gehe dabei auf die wichtigsten Punkte zur Vermögensbildung ein.

    Füge am Ende Empfehlungen für Gründer hinzu.
"""

researcher = GPTResearcher(
    query=query,
    report_type="research_report",
    report_source="langchain_vectorstore",
    vector_store=vector_store,
)

await researcher.conduct_research()
report = await researcher.write_report()
```

## PGVector

```python
from gpt_researcher import GPTResearcher
from langchain_postgres.vectorstores import PGVector
from langchain_openai import OpenAIEmbeddings

CONNECTION_STRING = 'postgresql://someuser:somepass@localhost:5432/somedatabase'

vector_store = PGVector.from_existing_index(
    use_jsonb=True,
    embedding=OpenAIEmbeddings(),
    collection_name='some collection name',
    connection=CONNECTION_STRING,
    async_mode=True,
)

query = """
    Erstelle einen kurzen Report über Äpfel.
    Füge einen Abschnitt dazu ein, welche Äpfel in welcher Jahreszeit
    als besonders gut gelten.
"""

researcher = GPTResearcher(
    query=query,
    report_type="research_report",
    report_source="langchain_vectorstore",
    vector_store=vector_store,
)

await researcher.conduct_research()
report = await researcher.write_report()
```

## Gescrapte Daten in den Vector Store schreiben

Wenn du gescrapte Daten und Dokumente für spätere Nutzung in deinem eigenen Vector Store speichern möchtest, kannst du GPT Researcher direkt mit einem Vector Store versorgen (achte darauf, `report_source` auf etwas anderes als `langchain_vectorstore` zu setzen).

```python
from gpt_researcher import GPTResearcher
from langchain_community.vectorstores import InMemoryVectorStore
from langchain_openai import OpenAIEmbeddings

vector_store = InMemoryVectorStore(embedding=OpenAIEmbeddings())

query = "The best LLM"

researcher = GPTResearcher(
    query=query,
    report_type="research_report",
    report_source="web",
    vector_store=vector_store,
)

await researcher.conduct_research()

related_contexts = await vector_store.asimilarity_search("GPT-4", k=5)
print(related_contexts)
print(len(related_contexts))
```
