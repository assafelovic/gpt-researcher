from gpt_researcher.config.config import Config
import os
from datetime import datetime
from dotenv import load_dotenv
import json
import logging
import inspect

# Set up logging to match existing format
def setup_logging():
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = f'logs/test_config_{timestamp}.log'
    
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Configure logging to write to both file and console with milliseconds
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s,%(msecs)03d - %(name)s - INFO - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    return logging.getLogger('research')

def trace_api_call(func):
    """Decorator to trace API calls"""
    def wrapper(*args, **kwargs):
        caller = inspect.currentframe().f_back.f_code.co_name
        logger = logging.getLogger('research')
        logger.info(f"API Call from {caller}: {func.__name__}")
        try:
            result = func(*args, **kwargs)
            logger.info(f"API Call successful: {func.__name__}")
            return result
        except Exception as e:
            logger.error(f"API Call failed: {func.__name__} - {str(e)}")
            raise
    return wrapper

def test_config():
    logger = setup_logging()
    load_dotenv()  # Restore this as we need env vars for API keys
    
    # Load config from custom file
    config_path = "configs/my_custom_config.json"
    logger.info(f"Loading config from: {config_path}")
    cfg = Config(config_path)
    
    # Log all LLM configurations
    logger.info("LLM Configuration:")
    logger.info(f"Fast LLM: {cfg.fast_llm_provider}:{cfg.fast_llm_model}")
    logger.info(f"Smart LLM: {cfg.smart_llm_provider}:{cfg.smart_llm_model}")
    logger.info(f"Strategic LLM: {cfg.strategic_llm_provider}:{cfg.strategic_llm_model}")
    
    # Log embedding configuration
    logger.info("Embedding Configuration:")
    logger.info(f"Provider: {cfg.embedding_provider}")
    logger.info(f"Model: {cfg.embedding_model}")
    
    # Log temperature configuration
    logger.info("Temperature configuration:")
    logger.info(f"Default LLM temperature: {cfg.llm_temperature}")
    logger.info(f"Fast LLM temperature: {cfg.fast_llm_temperature}")
    logger.info(f"Smart LLM temperature: {cfg.smart_llm_temperature}")
    logger.info(f"Strategic LLM temperature: {cfg.strategic_llm_temperature}")
    
    # Log other important settings
    logger.info("Other Settings:")
    logger.info(f"Max Iterations: {cfg.max_iterations}")
    logger.info(f"Max Subtopics: {cfg.max_subtopics}")
    logger.info(f"Language: {cfg.language}")
    logger.info(f"Retrievers: {cfg.retrievers}")
    logger.info(f"Document Path: {cfg.doc_path}")

    # Test LLM initialization
    logger.info("Testing LLM initialization:")
    logger.info(f"Fast LLM model type: {type(cfg.fast_llm_model)}")
    logger.info(f"Fast LLM model value: '{cfg.fast_llm_model}'")
    
    try:
        if cfg.fast_llm_model.startswith('gemini'):
            from langchain_google_genai import ChatGoogleGenerativeAI
            
            @trace_api_call
            def test_llm_call(llm, prompt):
                return llm.invoke(prompt)
            
            llm = ChatGoogleGenerativeAI(
                model="gemini-pro",
                temperature=cfg.fast_llm_temperature  # Use specific LLM temperature
            )
            logger.info("Successfully initialized Gemini LLM")
            
            # Test the LLM with tracing
            response = test_llm_call(llm, "Hello, are you working?")
            logger.info(f"Test response: {response}")
        else:
            logger.info(f"Not configured for Gemini: {cfg.fast_llm_model}")
    except Exception as e:
        logger.error(f"Error initializing Gemini: {e}")
    
    # Print all environment variables related to APIs
    logger.info("API Keys present:")
    for key in os.environ:
        if 'API' in key:
            logger.info(f"{key}: {'[SET]' if os.environ[key] else '[NOT SET]'}")

if __name__ == "__main__":
    test_config()