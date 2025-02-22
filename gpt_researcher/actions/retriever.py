from __future__ import annotations

import logging

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from langchain_core.retrievers import BaseRetriever

    from gpt_researcher.config.config import Config


logger = logging.getLogger(__name__)


def get_retriever(
    retriever: str | type[BaseRetriever] | None = None,
) -> type[BaseRetriever]:
    """Gets the retriever.

    Args:
    ----
        retriever (str | type[BaseRetriever] | None) : retriever name.

    Returns:
    -------
        retriever (BaseRetriever): Retriever class
    """
    # TODO(th3w1zard1): currently static typed as a BaseRetriever, however this is intended for the future
    # The goal is to migrate GPT Researcher's retrievers to use LangChain's BaseModel ABC.
    # This will also allow for more flexibility in the future, and improving new contributors' experience overall if they're already familiar with LangChain.
    retriever = get_langchain_retriever(retriever)
    if retriever is not None and not isinstance(retriever, str):
        return retriever

    if retriever == "bing":
        from gpt_researcher.retrievers import BingSearch

        return BingSearch
    if retriever == "custom":
        from gpt_researcher.retrievers import CustomRetriever

        return CustomRetriever  # type: ignore[return-value]
    if retriever == "duckduckgo":
        from gpt_researcher.retrievers import Duckduckgo

        return Duckduckgo  # type: ignore[return-value]
    if retriever == "exa":
        from gpt_researcher.retrievers import ExaSearch

        return ExaSearch  # type: ignore[return-value]
    if retriever == "google":
        from gpt_researcher.retrievers import GoogleSearch

        return GoogleSearch  # type: ignore[return-value]
    if retriever == "searchapi":
        from gpt_researcher.retrievers import SearchApiSearch

        return SearchApiSearch  # type: ignore[return-value]
    if retriever == "searx":
        from gpt_researcher.retrievers import SearxSearch

        return SearxSearch  # type: ignore[return-value]
    if retriever == "semantic_scholar":
        from gpt_researcher.retrievers import SemanticScholarSearch

        return SemanticScholarSearch  # type: ignore[return-value]
    if retriever is None:
        return get_default_retriever()
    raise ValueError(f"Retriever {retriever} not found")


def get_langchain_retriever(
    retriever: str | type[BaseRetriever] | None = None,
) -> str | type[BaseRetriever] | None:
    if isinstance(retriever, type) and issubclass(retriever, BaseRetriever):
        return retriever

    if retriever == "arcee":
        from langchain_community.retrievers import ArceeRetriever

        return ArceeRetriever
    if retriever == "arxiv":
        from langchain_community.retrievers import ArxivRetriever

        return ArxivRetriever
    if retriever == "asknews":
        from langchain_community.retrievers import AskNewsRetriever

        return AskNewsRetriever
    if retriever == "azure_ai_search":
        from langchain_community.retrievers import AzureAISearchRetriever

        return AzureAISearchRetriever
    if retriever == "azure_cognitive_search":
        from langchain_community.retrievers import AzureCognitiveSearchRetriever

        return AzureCognitiveSearchRetriever
    if retriever == "bedrock":
        from langchain_community.retrievers import AmazonKnowledgeBasesRetriever

        return AmazonKnowledgeBasesRetriever
    if retriever == "bm25":
        from langchain_community.retrievers import BM25Retriever

        return BM25Retriever
    if retriever == "breebs":
        from langchain_community.retrievers import BreebsRetriever

        return BreebsRetriever
    if retriever == "chaindesk":
        from langchain_community.retrievers import ChaindeskRetriever

        return ChaindeskRetriever
    if retriever == "chatgpt_plugin":
        from langchain_community.retrievers import ChatGPTPluginRetriever

        return ChatGPTPluginRetriever
    if retriever == "cohere_rag":
        from langchain_community.retrievers import CohereRagRetriever

        return CohereRagRetriever
    if retriever == "docarray":
        from langchain_community.retrievers import DocArrayRetriever

        return DocArrayRetriever
    if retriever == "dria":
        from langchain_community.retrievers import DriaRetriever

        return DriaRetriever
    if retriever == "elastic_search_bm25":
        from langchain_community.retrievers import ElasticSearchBM25Retriever

        return ElasticSearchBM25Retriever
    if retriever == "embedchain":
        from langchain_community.retrievers import EmbedchainRetriever

        return EmbedchainRetriever
    if retriever == "google_cloud_documentai_warehouse":
        from langchain_community.retrievers import GoogleDocumentAIWarehouseRetriever

        return GoogleDocumentAIWarehouseRetriever
    if retriever == "google_cloud_enterprise_search":
        from langchain_community.retrievers import GoogleCloudEnterpriseSearchRetriever

        return GoogleCloudEnterpriseSearchRetriever
    if retriever == "google_vertex_ai_search":
        from langchain_community.retrievers import GoogleVertexAISearchRetriever

        return GoogleVertexAISearchRetriever
    if retriever == "kay":
        from langchain_community.retrievers import KayAiRetriever

        return KayAiRetriever
    if retriever == "kendra":
        from langchain_community.retrievers import AmazonKendraRetriever

        return AmazonKendraRetriever
    if retriever == "knn":
        from langchain_community.retrievers import KNNRetriever

        return KNNRetriever
    if retriever == "llama_index":
        from langchain_community.retrievers import LlamaIndexRetriever

        return LlamaIndexRetriever
    if retriever == "metal":
        from langchain_community.retrievers import MetalRetriever

        return MetalRetriever
    if retriever == "milvus":
        from langchain_community.retrievers import MilvusRetriever

        return MilvusRetriever
    if retriever == "nanopq":
        from langchain_community.retrievers import NanoPQRetriever

        return NanoPQRetriever
    if retriever == "needle":
        from langchain_community.retrievers import NeedleRetriever

        return NeedleRetriever
    if retriever == "outline":
        from langchain_community.retrievers import OutlineRetriever

        return OutlineRetriever
    if retriever == "pinecone_hybrid_search":
        from langchain_community.retrievers import PineconeHybridSearchRetriever

        return PineconeHybridSearchRetriever
    if retriever == "pubmed":
        from langchain_community.retrievers import PubMedRetriever

        return PubMedRetriever
    if retriever == "qdrant_sparse_vector":
        from langchain_community.retrievers import QdrantSparseVectorRetriever

        return QdrantSparseVectorRetriever
    if retriever == "rememberizer":
        from langchain_community.retrievers import RememberizerRetriever

        return RememberizerRetriever
    if retriever == "remote":
        from langchain_community.retrievers import RemoteLangChainRetriever

        return RemoteLangChainRetriever
    if retriever == "svm":
        from langchain_community.retrievers import SVMRetriever

        return SVMRetriever
    if retriever == "tavily":
        from langchain_community.retrievers import TavilySearchAPIRetriever

        return TavilySearchAPIRetriever
    if retriever == "tfidf":
        from langchain_community.retrievers import TFIDFRetriever

        return TFIDFRetriever
    if retriever == "thirdai_neuraldb":
        from langchain_community.retrievers import NeuralDBRetriever

        return NeuralDBRetriever
    if retriever == "vespa":
        from langchain_community.retrievers import VespaRetriever

        return VespaRetriever
    if retriever == "weaviate_hybrid_search":
        from langchain_community.retrievers import WeaviateHybridSearchRetriever

        return WeaviateHybridSearchRetriever
    if retriever == "wikipedia":
        from langchain_community.retrievers import WikipediaRetriever

        return WikipediaRetriever
    if retriever == "you":
        from langchain_community.retrievers import YouRetriever

        return YouRetriever
    if retriever == "zep":
        from langchain_community.retrievers import ZepRetriever

        return ZepRetriever
    if retriever == "zep_cloud":
        from langchain_community.retrievers import ZepCloudRetriever

        return ZepCloudRetriever
    if retriever == "zilliz":
        from langchain_community.retrievers import ZillizRetriever

        return ZillizRetriever

    logger.warning(f"Retriever '{retriever}' not found in langchain's library.")
    return None


def get_retrievers(
    headers: dict,
    research_config: Config,
) -> list[type[BaseRetriever]]:
    """Determine which retriever(s) to use based on headers, config, or default.

    Args:
    ----
        headers (dict): The headers dictionary
        research_config (Config): The configuration object

    Returns:
    -------
        retrievers (list): A list of retriever classes to be used for searching.
    """
    # Check headers first for multiple retrievers
    if headers.get("retrievers"):
        retrievers = str(headers.get("retrievers")).split(",")
    # If not found, check headers for a single retriever
    elif headers.get("retriever"):
        retrievers = [headers.get("retriever")]
    # If not in headers, check config for multiple retrievers
    elif research_config.retrievers:
        retrievers = research_config.retrievers
    # If not found, check config for a single retriever
    elif research_config.RETRIEVER:  # type: ignore[attr-defined]
        retrievers = [research_config.RETRIEVER]  # type: ignore[attr-defined]
    # If still not set, use default retriever
    else:
        retrievers = [get_default_retriever().__name__]

    return [get_retriever(r) for r in retrievers]


def get_default_retriever() -> type[BaseRetriever]:
    from langchain_community.retrievers import TavilySearchAPIRetriever

    return TavilySearchAPIRetriever
