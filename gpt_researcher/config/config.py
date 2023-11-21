# config file
import json
from collections import OrderedDict


class Config:
    """Config class for GPT Researcher."""

    type_mapping = {
        "debug_mode": bool,
        "allow_downloads": bool,
        "selenium_web_browser": str,
        "retriever": str,
        "llm_provider": str,
        "fast_llm_model": str,
        "smart_llm_model": str,
        "fast_token_limit": int,
        "smart_token_limit": int,
        "browse_chunk_max_length": int,
        "summary_token_limit": int,
        "temperature": float,
        "user_agent": str,
        "max_search_results_per_query": int,
        "memory_backend": str,
        "total_words": int,
        "report_format": str,
        "max_iterations": int
    }
    key_order = type_mapping.keys()

    config_description  ={
        "debug_mode": " (NOT IMPLEMENTED)",
        "allow_downloads": "(NOT IMPLEMENTED)",
        "selenium_web_browser": "",
        "retriever": "",
        "llm_provider": "",
        "fast_llm_model": "",
        "smart_llm_model": "",
        "fast_token_limit": "(NOT IMPLEMENTED)",
        "smart_token_limit": "(NOT IMPLEMENTED)",
        "browse_chunk_max_length": "",
        "summary_token_limit": "",
        "temperature": "creativity measure",
        "user_agent": "",
        "max_search_results_per_query":"",
        "memory_backend": "",
        "total_words": "Minimum Total words in Report",
        "report_format": "",
        "max_iterations": "Number of phrases generated then searched"
    }

    def __init__(self, config_file: str = None):
        """Initialize the config class."""
        self.config_file = config_file
        self.retriever = "tavily"
        self.llm_provider = "ChatOpenAI"
        self.fast_llm_model = "gpt-3.5-turbo-16k"
        self.smart_llm_model = "gpt-4-1106-preview"
        self.fast_token_limit = 2000
        self.smart_token_limit = 1000
        self.browse_chunk_max_length = 8192
        self.summary_token_limit = 700
        self.temperature = 0.55
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)" \
                          " Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0"
        self.max_search_results_per_query = 5
        self.memory_backend = "local"
        self.total_words = 10000 
        self.report_format = "apa"
        self.max_iterations = 3

        self.load_config_file()

    def load_config_file(self) -> None:
        """Load the config file."""

        if self.config_file is None:
            self.config_file="config.json"
        with open(self.config_file, "r") as f:
            config = json.load(f)
        for key, value in config.items():
            self.__dict__[key] = value

    @staticmethod
    def read_config_from_file(file_path: str = 'config.json'):
        with open(file_path, 'r') as config_file:
            config_data = json.load(config_file)
            # OrderedDictionaries are required for the config file to be written in the correct order
            ordered_config_data = OrderedDict()
            for key in Config.key_order:
                ordered_config_data[key] = Config.type_mapping[key](config_data[key])
            return ordered_config_data

    @staticmethod
    def write_config_to_file(config_dict: dict):
        ordered_config_data = OrderedDict([(key, config_dict[key]) for key in Config.key_order])
        with open('config.json', 'w') as config_file:
            json.dump(ordered_config_data, config_file, indent=4)
