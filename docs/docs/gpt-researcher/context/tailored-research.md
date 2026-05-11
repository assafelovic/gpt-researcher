# Maßgeschneiderte Recherche

GPT Researcher kann nicht nur das Web durchsuchen, sondern auch mit lokalen Dokumenten, Vector Stores und Azure Blob Storage arbeiten. So kannst du den Recherchekontext an deine eigenen Daten anpassen.

## Verfügbare Quellen

- **Web**: klassische Online-Recherche
- **Lokale Dokumente**: Recherche auf Dateien im lokalen Ordner
- **Hybrid**: Kombination aus Web und lokalen Dokumenten
- **LangChain Documents**: direkte Recherche auf vorhandenen Dokumentobjekten
- **LangChain VectorStores**: Recherche auf einem vorhandenen Vector Store
- **Azure Storage**: Recherche auf Dokumenten in Azure Blob Storage

## Typische Nutzung

Wähle die passende Quelle je nach Anwendungsfall:

- Nutze `web`, wenn du aktuelle Online-Informationen suchst
- Nutze `local`, wenn du auf eigene Dateien zugreifen willst
- Nutze `hybrid`, wenn du beides kombinieren möchtest
- Nutze `langchain_documents` oder `langchain_vectorstore`, wenn deine Daten bereits in LangChain vorliegen
- Nutze `azure`, wenn deine Dokumente in Azure Blob Storage liegen

## Weitere Details

Die konkreten Anleitungen findest du auf den Seiten:
- [Lokale Dokumente](/docs/gpt-researcher/context/local-docs)
- [Azure Storage](/docs/gpt-researcher/context/azure-storage)
- [Filterung nach Domäne](/docs/gpt-researcher/context/filtering-by-domain)
- [Vector Stores](/docs/gpt-researcher/context/vector-stores)
- [Data Ingestion](/docs/gpt-researcher/context/data-ingestion)
