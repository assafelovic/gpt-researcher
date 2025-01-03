from gpt_researcher.config.config import Config
from gpt_researcher.skills.researcher import ResearchConductor
import os
from datetime import datetime
from dotenv import load_dotenv
import logging
import inspect
import asyncio
import sys
from types import SimpleNamespace
import json

# Create a mock retriever class
class MockRetriever:
    def __init__(self, query):
        self.query = query
    
    def search(self, max_results=5):
        return [{"href": "https://example.com", "title": "Test Result"}]

# Add this class after MockRetriever
class MockScraperManager:
    async def browse_urls(self, urls):
        return [{
            "url": "https://example.com",
            "title": "Test Page",
            "text": "Sample text about space events in 2024 including solar eclipses and meteor showers."
        }]

class MockContextManager:
    async def get_similar_content_by_query(self, query, content):
        return "Relevant content about " + query

def setup_logging():
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = f'logs/test_research_{timestamp}.log'
    
    os.makedirs('logs', exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s,%(msecs)03d - %(name)s - INFO - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    return logging.getLogger('research')

def trace_api_call(func):
    """Decorator to trace API calls with more detail"""
    async def wrapper(*args, **kwargs):
        caller_frame = inspect.currentframe().f_back
        caller_name = caller_frame.f_code.co_name
        module_name = inspect.getmodule(caller_frame).__name__
        
        logger = logging.getLogger('research')
        logger.info(f"API Call from {module_name}.{caller_name}")
        logger.info(f"Function: {func.__name__}")
        logger.info(f"Args: {args}")
        logger.info(f"Kwargs: {kwargs}")
        
        try:
            if inspect.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            logger.info(f"API Call successful: {func.__name__}")
            return result
        except Exception as e:
            logger.error(f"API Call failed: {func.__name__} - {str(e)}")
            raise
    return wrapper if inspect.iscoroutinefunction(func) else sync_wrapper

def sync_wrapper(*args, **kwargs):
    return asyncio.run(wrapper(*args, **kwargs))

class MockLLM:
    """Mock LLM to trace calls with model verification"""
    def __init__(self, model_name):
        self.model_name = model_name
        self.logger = logging.getLogger('research')
        self.calls = []  # Track all calls
        
        # Expected configuration
        self.expected_config = {
            'gemini-pro': {
                'temperature': 0.7,
                'max_tokens': 4000,
            }
        }
    
    def _verify_config(self, **kwargs):
        """Verify the LLM is configured correctly"""
        model = kwargs.get('model', self.model_name)
        expected = self.expected_config.get(model, {})
        
        self.logger.info(f"Verifying {model} configuration:")
        self.logger.info(f"Expected: {expected}")
        self.logger.info(f"Received: {kwargs}")
        
        if model != 'gemini-pro':
            self.logger.error(f"Wrong model: {model}, expected gemini-pro")
        
        if kwargs.get('temperature') != expected.get('temperature'):
            self.logger.error(f"Wrong temperature: {kwargs.get('temperature')}, expected {expected.get('temperature')}")
    
    @trace_api_call
    async def ainvoke(self, messages, **kwargs):
        self.logger.info(f"LLM ainvoke Call to {self.model_name}")
        self.logger.info(f"Messages: {messages}")
        
        # Track this call
        self.calls.append({
            'method': 'ainvoke',
            'messages': messages,
            'kwargs': kwargs
        })
        
        # Verify configuration
        self._verify_config(**kwargs)
        
        # Return mock response
        return SimpleNamespace(
            content=f"['Major space events 2024', 'Upcoming space missions 2024', 'Space mission schedule 2024']",
            additional_kwargs={},
            example=False,
            generation_info=None,
            type="ChatGeneration"
        )
    
    @trace_api_call
    async def agenerate(self, *args, **kwargs):
        self.logger.info(f"LLM Call to {self.model_name}")
        self.logger.info(f"Prompt: {kwargs.get('prompt', 'No prompt found')}")
        return [{
            "text": f"Mock response from {self.model_name}",
            "finish_reason": "stop"
        }]
    
    @trace_api_call
    async def acreate(self, *args, **kwargs):
        self.logger.info(f"LLM Create Call to {self.model_name}")
        self.logger.info(f"Messages: {kwargs.get('messages', 'No messages found')}")
        return {
            "choices": [{
                "message": {"content": f"Mock response from {self.model_name}"},
                "finish_reason": "stop"
            }]
        }
    
    def __call__(self, *args, **kwargs):
        self.logger.info(f"Direct Call to {self.model_name}")
        return f"Mock direct response from {self.model_name}"

class MockResearcher:
    def __init__(self, query, config, report_type):
        self.query = query
        self.cfg = config
        self.report_type = report_type
        self.verbose = True
        self.websocket = None
        self.visited_urls = set()
        self.context = ""
        self.role = None
        self.parent_query = None
        self.retrievers = [MockRetriever]
        self.source_urls = []
        self.complement_source_urls = False
        self.report_source = "web"
        self.vector_store = None
        self.documents = None
        self.vector_store_filter = None
        self.source_curator = None
        self.context_manager = MockContextManager()
        self.scraper_manager = MockScraperManager()
        self.agent = "Research Agent"
        self.add_costs = lambda x: None
        self.get_costs = lambda: 0.0
        
        # Add LLM tracing with proper interface
        self.llm = MockLLM(self.cfg.fast_llm_model)  # Main LLM instance
        self.fast_llm = self.llm
        self.smart_llm = MockLLM(self.cfg.smart_llm_model)
        self.strategic_llm = MockLLM(self.cfg.strategic_llm_model)

def patch_langchain():
    """Patch LangChain to use our mock LLMs with verification"""
    logger = logging.getLogger('research')
    logger.info("Starting LangChain patching...")
    
    def mock_llm_factory(*args, **kwargs):
        logger.info("Mock factory called with:")
        logger.info("  - args: %s", args)
        logger.info("  - kwargs: %s", kwargs)
        
        # Get the model name from the correct parameter
        model = kwargs.get('model_name', kwargs.get('model', 'default-mock-model'))
        logger.info("  - selected model: %s", model)
        
        # Log temperature setting
        temp = kwargs.get('temperature')
        logger.info(f"  - temperature: {temp}")
        
        if model != 'gemini-pro':
            logger.error(f"Wrong model selected: {model}")
        
        mock_llm = MockLLM(model)
        mock_llm._verify_config(**kwargs)
        logger.info(f"Created mock LLM for model: {model}")
        return mock_llm
    
    try:
        import langchain_community.chat_models
        import langchain_community.llms
        import langchain_google_genai
        
        # Patch the LLM classes
        langchain_community.chat_models.ChatOpenAI = mock_llm_factory
        langchain_community.llms.OpenAI = mock_llm_factory
        langchain_google_genai.ChatGoogleGenerativeAI = mock_llm_factory
        
        logger.info("Successfully patched:")
        logger.info("  - ChatOpenAI")
        logger.info("  - OpenAI")
        logger.info("  - ChatGoogleGenerativeAI")
    except Exception as e:
        logger.error(f"Error patching LangChain: {e}")
        raise

async def test_research_config():
    load_dotenv()
    logger = setup_logging()
    
    # Get config path from environment, fallback to default if not specified
    config_path = os.getenv('CONFIG_PATH')
    logger.info(f"Loading research config from: {config_path or 'default config'}")
    cfg = Config(config_path)
    
    # Load the actual config file content to check source of values
    with open(config_path) as f:
        config_content = json.load(f)
    
    # Define all expected settings from default_config.json
    expected_settings = {
        "LLM Models": ["FAST_LLM", "SMART_LLM", "STRATEGIC_LLM"],
        "Embedding": ["EMBEDDING"],
        "Token Limits": ["FAST_TOKEN_LIMIT", "SMART_TOKEN_LIMIT", "STRATEGIC_TOKEN_LIMIT", 
                        "BROWSE_CHUNK_MAX_LENGTH", "SUMMARY_TOKEN_LIMIT"],
        "Temperature Settings": ["TEMPERATURE", "LLM_TEMPERATURE", "FAST_LLM_TEMPERATURE", 
                               "SMART_LLM_TEMPERATURE", "STRATEGIC_LLM_TEMPERATURE"],
        "Research Settings": ["MAX_ITERATIONS", "MAX_SUBTOPICS", "MAX_SEARCH_RESULTS_PER_QUERY", 
                            "TOTAL_WORDS", "SIMILARITY_THRESHOLD"],
        "General Settings": ["LANGUAGE", "RETRIEVERS", "DOC_PATH", "MEMORY_BACKEND", 
                           "REPORT_FORMAT", "CURATE_SOURCES", "AGENT_ROLE", "SCRAPER", 
                           "REPORT_SOURCE", "USER_AGENT"]
    }
    
    # Check each setting group
    for group, settings in expected_settings.items():
        logger.info(f"\n{group}:")
        for setting in settings:
            try:
                value = getattr(cfg, setting.lower())
                if setting in config_content:
                    source = "config file"
                elif os.getenv(setting):
                    source = "environment variable"
                else:
                    source = "default config"
                logger.info(f"  - {setting}: {value} (from {source})")
            except AttributeError:
                logger.warning(f"  - {setting}: UNDECLARED (not available in Config class)")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_research_config())