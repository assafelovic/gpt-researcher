from ..config.config import Config

def get_retriever(retriever: str):
    """
    Gets the retriever
    Args:
        retriever (str): retriever name

    Returns:
        retriever: Retriever class

    """
    match retriever:
        case "google":
            from gpt_researcher.retrievers import GoogleSearch

            return GoogleSearch
        case "searx":
            from gpt_researcher.retrievers import SearxSearch

            return SearxSearch
        case "searchapi":
            from gpt_researcher.retrievers import SearchApiSearch

            return SearchApiSearch
        case "serpapi":
            from gpt_researcher.retrievers import SerpApiSearch

            return SerpApiSearch
        case "serper":
            from gpt_researcher.retrievers import SerperSearch

            return SerperSearch
        case "duckduckgo":
            from gpt_researcher.retrievers import Duckduckgo

            return Duckduckgo
        case "bing":
            from gpt_researcher.retrievers import BingSearch

            return BingSearch
        case "arxiv":
            from gpt_researcher.retrievers import ArxivSearch

            return ArxivSearch
        case "tavily":
            from gpt_researcher.retrievers import TavilySearch

            return TavilySearch
        case "exa":
            from gpt_researcher.retrievers import ExaSearch

            return ExaSearch
        case "semantic_scholar":
            from gpt_researcher.retrievers import SemanticScholarSearch

            return SemanticScholarSearch
        case "pubmed_central":
            from gpt_researcher.retrievers import PubMedCentralSearch

            return PubMedCentralSearch
        case "custom":
            from gpt_researcher.retrievers import CustomRetriever

            return CustomRetriever

        case _:
            return None


def get_retrievers(headers: dict[str, str], cfg: Config):
    """
    Determine which retriever(s) to use based on headers, config, or default.

    Args:
        headers (dict): The headers dictionary
        cfg (Config): The configuration object

    Returns:
        list: A list of retriever classes to be used for searching.
    """
    retrievers = [] # Initialize an empty list

    # Check if focus_academic_medical_sources is True in cfg
    if getattr(cfg, 'focus_academic_medical_sources', False):
        retrievers = ["semantic_scholar", "pubmed_central", "arxiv"]
    else:
        # Fallback to existing logic if focus_academic_medical_sources is False or not set
        # Check headers first for multiple retrievers
        if headers.get("retrievers"):
            retrievers = headers.get("retrievers").split(",")
        # If not found, check headers for a single retriever
        elif headers.get("retriever"):
            retrievers = [headers.get("retriever")]
        # If not in headers, check config for multiple retrievers
        elif cfg.retrievers:
            retrievers = cfg.retrievers
        # If not found, check config for a single retriever
        elif cfg.retriever:
            retrievers = [cfg.retriever]
        # If still not set, use default retriever
        else:
            # Assuming get_default_retriever() returns the class itself, 
            # and we need its name for the list of strings.
            # However, the final list comprehension expects names, so this is fine.
            # The original code used get_default_retriever().__name__
            # Let's be consistent if this list is purely names before conversion.
            # The original logic implies 'retrievers' is a list of names.
            default_retriever_class = get_default_retriever()
            # Try to get the name; this might be tricky if it's not always a class with __name__
            # For simplicity, and given how other retrievers are specified (as strings),
            # let's assume the default should also be a string name here.
            # The default retriever is TavilySearch, so its name is "tavily".
            # This part is a bit tricky as the original code structure was a bit inconsistent.
            # Given the final line: `[get_retriever(r) or get_default_retriever() for r in retrievers]`
            # `retrievers` must be a list of strings.
            retrievers = ["tavily"] # Defaulting to "tavily" as a string name.
                                    # This matches the default retriever's expected name.

    # Convert retriever names to actual retriever classes
    # Use get_default_retriever() as a fallback for any invalid retriever names
    return [get_retriever(r) or get_default_retriever() for r in retrievers]


def get_default_retriever():
    from gpt_researcher.retrievers import TavilySearch

    return TavilySearch