# config file
import json
import os


class Config:
    """Config class for GPT Researcher."""

    def __init__(self, config_file: str = None):
        """Initialize the config class."""
        self.config_file = os.path.expanduser(config_file) if config_file else os.getenv('CONFIG_FILE')
        self.retriever = os.getenv('RETRIEVER', "tavily")
        self.embedding_provider = os.getenv('EMBEDDING_PROVIDER', 'openai')
        self.similarity_threshold = int(os.getenv('SIMILARITY_THRESHOLD', 0.38))
        self.llm_provider = os.getenv('LLM_PROVIDER', "openai")
        self.ollama_base_url = os.getenv('OLLAMA_BASE_URL', None)
        self.fast_llm_model = os.getenv('FAST_LLM_MODEL', "gpt-3.5-turbo-16k")
        self.smart_llm_model = os.getenv('SMART_LLM_MODEL', "gpt-4o")
        self.fast_token_limit = int(os.getenv('FAST_TOKEN_LIMIT', 2000))
        self.smart_token_limit = int(os.getenv('SMART_TOKEN_LIMIT', 4000))
        self.browse_chunk_max_length = int(os.getenv('BROWSE_CHUNK_MAX_LENGTH', 8192))
        self.summary_token_limit = int(os.getenv('SUMMARY_TOKEN_LIMIT', 700))
        self.temperature = float(os.getenv('TEMPERATURE', 0.55))
        self.user_agent = os.getenv('USER_AGENT', "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                                                   "(KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0")
        self.max_search_results_per_query = int(os.getenv('MAX_SEARCH_RESULTS_PER_QUERY', 5))
        self.memory_backend = os.getenv('MEMORY_BACKEND', "local")
        self.total_words = int(os.getenv('TOTAL_WORDS', 800))
        self.report_format = os.getenv('REPORT_FORMAT', "APA")
        self.max_iterations = int(os.getenv('MAX_ITERATIONS', 3))
        self.agent_role = os.getenv('AGENT_ROLE', None)
        self.scraper = os.getenv("SCRAPER", "bs")
        self.max_subtopics = os.getenv("MAX_SUBTOPICS", 3)
        self.doc_path = os.getenv("DOC_PATH", "")

        self.load_config_file()
        if not hasattr(self, "llm_kwargs"):
            self.llm_kwargs = {}

        if self.doc_path:
            self.validate_doc_path()
        
    def validate_doc_path(self):
        """Ensure that the folder exists at the doc path"""
        os.makedirs(self.doc_path, exist_ok=True)

    def load_config_file(self) -> None:
        """Load the config file."""
        if self.config_file is None:
            return None
        with open(self.config_file, "r") as f:
            config = json.load(f)
        for key, value in config.items():
            setattr(self, key.lower(), value)