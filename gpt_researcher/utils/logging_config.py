import logging
import json
import os
from datetime import datetime
from pathlib import Path

class JSONResearchHandler:
    def __init__(self, json_file):
        self.json_file = json_file
        self.research_data = {
            "timestamp": datetime.now().isoformat(),
            "events": [],
            "content": {
                "query": "",
                "sources": [],
                "context": [],
                "report": "",
                "costs": 0.0
            }
        }

    def log_event(self, event_type: str, data: dict):
        self.research_data["events"].append({
            "timestamp": datetime.now().isoformat(),
            "type": event_type,
            "data": data
        })
        self._save_json()

    def update_content(self, key: str, value):
        self.research_data["content"][key] = value
        self._save_json()

    def _save_json(self):
        with open(self.json_file, 'w') as f:
            json.dump(self.research_data, f, indent=2)

def setup_research_logging():
    # Create logs directory if it doesn't exist
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Generate timestamp for log files
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create log file paths
    log_file = logs_dir / f"research_{timestamp}.log"
    json_file = logs_dir / f"research_{timestamp}.json"
    
    # Configure file handler for research logs
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    
    # Get research logger and configure it
    research_logger = logging.getLogger('research')
    research_logger.setLevel(logging.INFO)
    
    # Remove any existing handlers to avoid duplicates
    research_logger.handlers.clear()
    
    # Add file handler
    research_logger.addHandler(file_handler)
    
    # Add stream handler for console output
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    research_logger.addHandler(console_handler)
    
    # Prevent propagation to root logger to avoid duplicate logs
    research_logger.propagate = False
    
    # Create JSON handler
    json_handler = JSONResearchHandler(json_file)
    
    return str(log_file), str(json_file), research_logger, json_handler

def get_research_logger():
    return logging.getLogger('research')

def get_json_handler():
    return getattr(logging.getLogger('research'), 'json_handler', None)
