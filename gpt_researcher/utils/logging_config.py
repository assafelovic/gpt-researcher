import logging
import json
from datetime import datetime
from pathlib import Path

from .artifacts import make_unique_artifact_stem

ARTIFACTS_DIR = Path("outputs")

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
        self._save_json()

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
        json_path = Path(self.json_file)
        json_path.parent.mkdir(parents=True, exist_ok=True)
        with json_path.open('w') as f:
            json.dump(self.research_data, f, indent=2)

def setup_research_logging():
    # Create the research artifact directory if it doesn't exist.
    artifacts_dir = ARTIFACTS_DIR
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate a collision-resistant stem for the research artifact files.
    artifact_stem = make_unique_artifact_stem("research", "session")
    
    # Create research artifact file paths.
    log_file = artifacts_dir / f"{artifact_stem}.log"
    json_file = artifacts_dir / f"{artifact_stem}.json"
    
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
    research_logger.json_handler = json_handler
    research_logger.log_file = str(log_file)
    research_logger.json_file = str(json_file)
    research_logger.output_dir = str(artifacts_dir)
    
    return str(log_file), str(json_file), research_logger, json_handler

def get_research_logger():
    return logging.getLogger('research')

def get_json_handler():
    return getattr(logging.getLogger('research'), 'json_handler', None)
