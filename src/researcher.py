from typing import Dict, Any
import json
from datetime import datetime
from pathlib import Path
import logging
import sys
from .logs_handler import CustomLogsHandler
from gpt_researcher.agent import GPTResearcher
from backend.server.logging_config import get_research_logger

# Configure logging to output to both file and console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('researcher_debug.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class ResearchLogHandler:
    """Custom handler to capture GPTResearcher logs"""
    def __init__(self, research_logger):
        self.logger = research_logger

    async def on_tool_start(self, tool_name: str, **kwargs):
        self.logger.info(f"Starting tool: {tool_name}")
        self.logger.info(f"Tool parameters: {kwargs}")

    async def on_tool_end(self, tool_name: str, result: Any):
        self.logger.info(f"Completed tool: {tool_name}")
        self.logger.info(f"Tool result: {result}")

    async def on_agent_action(self, action: str, **kwargs):
        self.logger.info(f"Agent action: {action}")
        self.logger.info(f"Action details: {kwargs}")

    async def on_research_step(self, step: str, details: Any):
        self.logger.info(f"Research step: {step}")
        self.logger.info(f"Step details: {details}")

class Researcher:
    def __init__(self, query: str, report_type: str = "research_report"):
        self.research_logger = get_research_logger()
        self.query = query
        self.report_type = report_type
        
        # Initialize our custom logs handler
        self.logs_handler = CustomLogsHandler()
        self.research_logger.info(f"Initialized Researcher with query: {query}")
        
        try:
            # Initialize research log handler
            self.research_log_handler = ResearchLogHandler(self.research_logger)
            
            # Initialize GPTResearcher with both handlers
            self.researcher = GPTResearcher(
                query=query,
                report_type=report_type,
                websocket=self.logs_handler,
                log_handler=self.research_log_handler  # Add research log handler
            )
            self.research_logger.info("Successfully initialized GPTResearcher")
        except Exception as e:
            self.research_logger.error(f"Error initializing GPTResearcher: {e}", exc_info=True)
            raise

    async def research(self) -> str:
        """Conduct research and return the report"""
        try:
            self.research_logger.info(f"Starting research process for query: {self.query}")
            self.research_logger.info(f"Report type: {self.report_type}")
            
            self.research_logger.info("Beginning research phase")
            await self.researcher.conduct_research()
            self.research_logger.info("Research phase completed")
            
            self.research_logger.info("Starting report generation")
            report = await self.researcher.write_report()
            self.research_logger.info("Report generation completed")
            
            # Log report summary
            report_preview = report[:500] + "..." if len(report) > 500 else report
            self.research_logger.info(f"Report preview: {report_preview}")
            
            return report
            
        except Exception as e:
            self.research_logger.error(f"Error during research: {e}", exc_info=True)
            raise

# ... rest of the code ...