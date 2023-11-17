from langchain.embeddings import OpenAIEmbeddings
from retriever import SearchAPIRetriever
from langchain.retrievers import (
    ContextualCompressionRetriever,
)
from langchain.retrievers.document_compressors import (
    DocumentCompressorPipeline,
    EmbeddingsFilter,
)
from langchain.text_splitter import RecursiveCharacterTextSplitter


class ContextCompressor():
    def __init__(self, documents, max_results=5, **kwargs):
        self.max_results = max_results
        self.documents = documents
        self.kwargs = kwargs

    def _get_contextual_retriever(self):
        embeddings = OpenAIEmbeddings()
        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        relevance_filter = EmbeddingsFilter(embeddings=embeddings, similarity_threshold=0.8)
        pipeline_compressor = DocumentCompressorPipeline(
            transformers=[splitter, relevance_filter]
        )
        base_retriever = SearchAPIRetriever(
            pages=self.documents
        )
        contextual_retriever = ContextualCompressionRetriever(
            base_compressor=pipeline_compressor, base_retriever=base_retriever
        )
        return contextual_retriever

    def _pretty_print_docs(self, docs, top_n):
        return f"\n\n".join(d.page_content for i, d in enumerate(docs) if i < top_n)

    def get_context(self, query):
        compressed_docs = self._get_contextual_retriever()
        relevant_docs = compressed_docs.get_relevant_documents(query)
        return self._pretty_print_docs(relevant_docs, 5)

bla = ContextCompressor(documents=[
    {"raw_content": "Donald trump rocks", "title": "Donald trump bio", "url": "https://donald.com"},
    {"raw_content": "Michael Jordan is a basketball player", "title": "MJ bio", "url": "https://mj.com"},
    {"raw_content": "Donald Trump is going to prison", "title": "Donald prison", "url": "https://wikipedia.com"},
])

print(bla.get_context("Who is donald trump?"))