# Mit Azure ausführen

## Beispiel: Azure-OpenAI-Konfiguration

Wenn du nicht die Modelle von OpenAI selbst nutzt, sondern andere Modellanbieter, brauchst du neben der allgemeinen Konfiguration zusätzliche Umgebungsvariablen.

Hier ist ein Beispiel für eine [Azure-OpenAI](https://learn.microsoft.com/en-us/azure/ai-services/openai/concepts/models)-Konfiguration:

```bash
OPENAI_API_VERSION="2024-05-01-preview" # oder die von dir verwendete Version
AZURE_OPENAI_ENDPOINT="https://CHANGEMEN.openai.azure.com/" # an den Namen deines Deployments anpassen
AZURE_OPENAI_API_KEY="[Dein Key]" # an deinen API-Key anpassen

EMBEDDING="azure_openai:text-embedding-ada-002" # an das Deployment deines Embedding-Modells anpassen

FAST_LLM="azure_openai:gpt-4o-mini" # an den Namen deines Deployments anpassen, nicht an den Modellnamen
FAST_TOKEN_LIMIT=4000

SMART_LLM="azure_openai:gpt-4o" # an den Namen deines Deployments anpassen, nicht an den Modellnamen
SMART_TOKEN_LIMIT=4000

RETRIEVER="bing" # wenn du Bing als Suchmaschine verwendest, was bei Azure oft der Fall ist
BING_API_KEY="[Dein Key]"
```

Weitere Details zu den einzelnen Variablen findest du in der [GPTR-Konfigurationsdokumentation](https://docs.gptr.dev/docs/gpt-researcher/gptr/config).
