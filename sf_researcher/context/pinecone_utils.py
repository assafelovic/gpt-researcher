# pinecone_utils/pinecone_manager.py

import os
import logging
from langchain.schema import Document
from langchain_pinecone import PineconeVectorStore
from langchain.indexes import SQLRecordManager, index
from langchain.text_splitter import RecursiveCharacterTextSplitter

from dotenv import load_dotenv
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PineconeManager:
    def __init__(self, index_name, embeddings, namespace):
        self.index_name = index_name
        self.embeddings = embeddings
        self.namespace = namespace
        self.api_key = self.get_api_key()
        self.pinecone_env = self.get_pinecone_env()
        self.vectorstore = PineconeVectorStore(
            index_name=self.index_name,
            embedding=self.embeddings,
            namespace=self.namespace,
        )
        self.record_manager = SQLRecordManager(
            namespace=f"pinecone/{self.index_name}/{self.namespace}",
            db_url=os.getenv("DATABASE_URL"),
        )
    
    def get_api_key(self):
        """
        Gets the Pinecone API key from the environment variable
        Returns:
            str: Pinecone API key
        """
        try:
            api_key = os.getenv("PINECONE_API_KEY")
        except KeyError:
            raise Exception("Pinecone API Key not found. Please set the PINECONE_API_KEY environment variable.")
        return api_key

    def get_pinecone_env(self):
        """
        Gets the Pinecone environment from the environment variable
        Returns:
            str: Pinecone environment
        """
        try:
            pinecone_env = os.getenv("PINECONE_ENVIRONMENT")
        except KeyError:
            raise Exception("Pinecone Environment not found. Please set the PINECONE_ENVIRONMENT environment variable.")
        return pinecone_env

    def process_scraped_content(self, scraped_content_results):
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=200)
        documents = []
        unique_urls = set()  # Track unique URLs
        for searchlist in scraped_content_results:
            for result in searchlist:
                url = result.get("url", "")
                if url not in unique_urls:
                    unique_urls.add(url)
                    raw_content = result.get("raw_content", "")
                    if raw_content:
                        chunks = text_splitter.split_text(raw_content)
                        for i, chunk in enumerate(chunks):
                            documents.append(
                                Document(
                                    page_content=chunk,
                                    metadata={
                                        "title": result.get("title", ""),
                                        "source": url,
                                        "source_type": "web_search",
                                        "chunk_index": i,
                                    },
                                )
                            )
                    else:
                        documents.append(
                            Document(
                                page_content="",
                                metadata={
                                    "title": result.get("title", ""),
                                    "source": url,
                                    "source_type": "web_search",
                                    "chunk_index": 0,
                                },
                            )
                        )
        return documents

    def insert_documents(self, documents):
        self.record_manager.create_schema()
        result = index(
            documents,
            record_manager=self.record_manager,
            vector_store=self.vectorstore,
            cleanup="incremental",
            source_id_key="source",
        )
        print(result)
        logger.info(f"\n🧩 Indexing result: {result}\n", )

    def query_documents_metadata(self, query):
        retriever = self.vectorstore.as_retriever()
        relevant_documents = retriever.get_relevant_documents(query)
        logger.info(f"\n🧩 pinecone_manager.py query_documents_metadata similarity_search results: {relevant_documents}\n")
        return relevant_documents
    
    def query_documents(self, query):
        relevant_documents = self.vectorstore.similarity_search(query, k=4)
        # logger.info(f"\n🧩 pinecone_manager.py similarity_search raw_results: \n{relevant_documents}\n")
        return relevant_documents