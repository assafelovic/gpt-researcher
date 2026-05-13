# Daten-Ingestion

Wenn du mit einer großen Menge an Kontextdaten arbeitest, lohnt sich oft ein eigener Ingestion-Prozess.

Einige Anzeichen dafür:

- Dein Embedding-Modell stößt an API-Rate-Limits
- Die Datenbank hinter deinem LangChain-VectorStore braucht Drosselung
- Du möchtest in deinem Python-Code eigenes Pacing oder Throttling einbauen

Wie in unserer [YouTube-Tutorialreihe](https://www.youtube.com/watch?v=yRuduRCblbg) beschrieben, nutzt GPTR intern [LangChain Documents](https://python.langchain.com/api_reference/core/documents/langchain_core.documents.base.Document.html) und [LangChain VectorStores](https://python.langchain.com/v0.1/docs/modules/data_connection/vectorstores/).

Der aktuelle Recherche-Flow ist:

```bash
Schritt 1: Inhalte (Web-Ergebnisse oder lokale Dokumente) in LangChain Documents umwandeln
```

```bash
Schritt 2: LangChain Documents in einen LangChain VectorStore schreiben
```

```bash
Schritt 3: Den LangChain VectorStore in deinen GPTR-Report übergeben
```

Beispiel-Umgebungsvariablen:

```bash
OPENAI_API_KEY={Your OpenAI API Key here}
TAVILY_API_KEY={Your Tavily API Key here}
PGVECTOR_CONNECTION_STRING=postgresql://username:password...
```

Unten findest du einen benutzerdefinierten Ingestion-Prozess, mit dem du Daten in einen LangChain-VectorStore laden kannst. Ein vollständiges Beispiel findest du [hier](https://github.com/assafelovic/gpt-researcher/pull/819#issue-2501632831).
In diesem Beispiel wird ein Postgres-VectorStore verwendet, um Daten aus einem GitHub-Branch zu speichern. Du kannst aber jeden unterstützten LangChain-VectorStore verwenden.

Wichtig: Wenn du die LangChain Documents erzeugst, solltest du als Metadaten die Felder `source` und `title` angeben, damit GPTR deine Dokumente sauber nutzen kann.

### Schritt 1: Inhalte in LangChain Documents umwandeln

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
                    print(f"Fehler beim Dekodieren des Inhalts: {e}")
                    print("Problematische Datei:", file_name)
                    continue
                print("Datei:", file_name)
                print("Inhalt:", decoded_content)

                chunks = splitter.split_text(decoded_content)

                for index, chunk in enumerate(chunks):
                    metadata = {
                        "id": f"{run_timestamp}_{uuid4()}",
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
                print(f"Fehler beim Speichern im Vector Store: {e}")
                return None

    await save_to_vector_store(documents)
```

### Schritt 2: LangChain Documents in einen LangChain VectorStore schreiben

```python
from langchain_postgres import PGVector
from langchain_postgres.vectorstores import PGVector
from sqlalchemy.ext.asyncio import create_async_engine
from langchain_community.embeddings import OpenAIEmbeddings

async def save_to_vector_store(self, documents):
    embeddings = OpenAIEmbeddings()
    pgvector_connection_string = os.environ["PGVECTOR_CONNECTION_STRING"]

    collection_name = "my_docs"

    vector_store = PGVector(
        embeddings=embeddings,
        collection_name=collection_name,
        connection=pgvector_connection_string,
        use_jsonb=True
    )

    for i in range(0, len(documents), 100):
        chunk = documents[i:i+100]
        vector_store.add_documents(chunk, ids=[doc.metadata["id"] for doc in chunk])
```

### Schritt 3: Den Vector Store in den GPTR-Report übergeben

```python
async_connection_string = pgvector_connection_string.replace("postgresql://", "postgresql+psycopg://")

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
