# Deinen Retriever testen

Mit folgendem Snippet kannst du prüfen, ob dein Retriever korrekt konfiguriert ist. Das Skript sucht nach einer Subquery und gibt die Suchergebnisse aus.

```python
import asyncio
from dotenv import load_dotenv
from gpt_researcher.config.config import Config
from gpt_researcher.actions.retriever import get_retrievers
from gpt_researcher.skills.researcher import ResearchConductor
import pprint

# Umgebungsvariablen aus der .env-Datei laden
load_dotenv()

async def test_scrape_data_by_query():
    # Config-Objekt initialisieren
    config = Config()

    # Retriever anhand der aktuellen Konfiguration abrufen
    retrievers = get_retrievers({}, config)
    print("Retriever:", retrievers)

    # Mock-Researcher mit den nötigen Attributen erstellen
    class MockResearcher:
        def init(self):
            self.retrievers = retrievers
            self.cfg = config
            self.verbose = True
            self.websocket = None
            self.scraper_manager = None
            self.vector_store = None

    researcher = MockResearcher()
    research_conductor = ResearchConductor(researcher)

    # Subquery zum Testen
    sub_query = "Designmuster für autonome KI-Agenten"

    # Alle Retriever durchlaufen
    for retriever_class in retrievers:
        # Retriever mit der Subquery instanziieren
        retriever = retriever_class(sub_query)

        # Suche ausführen
        search_results = await asyncio.to_thread(
            retriever.search, max_results=10
        )

        print("\033[35mSuchergebnisse:\033[0m")
        pprint.pprint(search_results, indent=4, width=80)

if __name__ == "__main__":
    asyncio.run(test_scrape_data_by_query())
```

Die Suchergebnisse enthalten Titel, Text und `href` jeder Quelle. Beispiel:

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
