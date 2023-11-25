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
        "llm_provider": "Name of LLM provider organization (ChatOpenAI, ChatAnthropic)",
        "fast_llm_model": "Model for webpage summarization (gpt-3.5-turbo-16k, gpt-4-1106-preview)",
        "smart_llm_model": "Model for report generation (gpt-3.5-turbo-16k, gpt-4-1106-preview)",
        "fast_token_limit": "(NOT IMPLEMENTED)",
        "smart_token_limit": "(NOT IMPLEMENTED)",
        "browse_chunk_max_length": "(NOT IMPLEMENTED)",
        "summary_token_limit": "(NOT IMPLEMENTED)",
        "temperature": "Creativity measure (0-1) (NOT IMPLEMENTED))",
        "user_agent": "",
        "max_search_results_per_query":"(NOT IMPLEMENTED)",
        "memory_backend": "",
        "total_words": "Minimum Total words in Report",
        "report_format": "Paper format (apa, ieee, MLA, ...)",
        "max_iterations": "Number of phrases generated then searched"
    }

    to_display = [
        "llm_provider",
        "fast_llm_model",
        "smart_llm_model",
        "total_words",
        "report_format",
        "max_iterations"
    ]

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

    @classmethod
    def get_config_description(cls, display_all: bool = False):
        # Filter the config description to only include the keys that are to_display
        print(cls,cls.to_display)
        if display_all:
            return cls.config_description
        else:
            return {key: cls.config_description[key] for key in cls.to_display}

    @classmethod 
    def get_config_types(cls,  display_all: bool = False):
        # Filter the config description to only include the keys that are to_display
        if display_all:
            return cls.type_mapping
        else:
            return {key: cls.type_mapping[key] for key in cls.to_display}
        

    @classmethod
    def read_config_from_file(cls,file_path: str = 'config.json', display_all: bool = False):
        with open(file_path, 'r') as config_file:
            config_data = json.load(config_file)
            if not display_all:
                config_data = {key: config_data[key] for key in cls.to_display}
                keys = cls.to_display
            else:
                keys = cls.key_order
            # OrderedDictionaries are required for the config file to be written in the correct order
            ordered_config_data = OrderedDict()
            for key in keys:
                config_map =  Config.get_config_types(display_all)
                ordered_config_data[key] = config_map[key](config_data[key])
    
            return ordered_config_data

    @classmethod
    def write_config_to_file(cls,  config_dict: dict):
        full_config= cls.read_config_from_file(display_all=True)
        full_config.update(config_dict)
        ordered_config_data = OrderedDict([(key, full_config[key]) for key in Config.key_order])
        with open('config.json', 'w') as config_file:
            json.dump(ordered_config_data, config_file, indent=4)
