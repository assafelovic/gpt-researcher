from tavily import Client
import os
from langchain.schema.runnable import RunnableLambda


class TavilySearchActor:
    def __init__(self):
        self.api_key = os.environ["TAVILY_API_KEY"]

    @property
    def runnable(self):
        client = Client(self.api_key)
        return RunnableLambda(client.advanced_search) | {"results": lambda x: x["results"]}
