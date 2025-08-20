"""
Verbose Manager for GPT Researcher

This module provides centralized verbose output management to ensure consistent
logging behavior across the entire application.
"""

import logging
import os
from typing import Optional, Any
from contextlib import contextmanager

class VerboseManager:
    """Manages verbose output across the application."""
    
    _instance = None
    _verbose = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._verbose is None:
            # Initialize from environment variable or default to True
            self._verbose = os.getenv("GPT_RESEARCHER_VERBOSE", "true").lower() == "true"
    
    @property
    def verbose(self) -> bool:
        """Get the current verbose setting."""
        return self._verbose
    
    @verbose.setter
    def verbose(self, value: bool):
        """Set the verbose flag."""
        self._verbose = value
        self._update_loggers()
    
    def _update_loggers(self):
        """Update all logger handlers based on verbose setting."""
        # Update research logger
        research_logger = logging.getLogger('research')
        self._update_logger_console_handlers(research_logger)
        
        # Update scraper logger
        scraper_logger = logging.getLogger('scraper')
        self._update_logger_console_handlers(scraper_logger)
        
        # Update root logger for other components
        root_logger = logging.getLogger()
        if not self._verbose:
            # Set root logger to WARNING when not verbose
            root_logger.setLevel(logging.WARNING)
        else:
            root_logger.setLevel(logging.INFO)
    
    def _update_logger_console_handlers(self, logger: logging.Logger):
        """Update console handlers for a specific logger."""
        # Remove existing console handlers
        console_handlers = [h for h in logger.handlers 
                          if isinstance(h, logging.StreamHandler) 
                          and h.stream.name == '<stderr>']
        
        for handler in console_handlers:
            logger.removeHandler(handler)
        
        # Add console handler only if verbose is True
        if self._verbose:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(
                logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            )
            logger.addHandler(console_handler)
    
    def print(self, message: str, *args, **kwargs):
        """Print message only if verbose mode is enabled."""
        if self._verbose:
            print(message, *args, **kwargs)
    
    def log(self, logger: logging.Logger, level: int, message: str, *args, **kwargs):
        """Log message with appropriate handling based on verbose mode."""
        if self._verbose or level >= logging.WARNING:
            logger.log(level, message, *args, **kwargs)
    
    @contextmanager
    def temporary_verbose(self, verbose: bool):
        """Temporarily change verbose setting."""
        original = self._verbose
        try:
            self.verbose = verbose
            yield
        finally:
            self.verbose = original

# Global instance
verbose_manager = VerboseManager()
