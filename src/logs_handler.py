import logging
import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

class CustomLogsHandler:
    """A unified custom logs handler for GPT Researcher."""
    
    def __init__(self, websocket=None, query=None):
        self.websocket = websocket
        self.query = query
        self.logs: List[Dict[str, Any]] = []
        
        # Set up logging configuration
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Initialize log file if query is provided
        if query:
            self.log_file = self._create_log_file()
    
    def _create_log_file(self):
        """Create log file with proper directory structure."""
        # Use the project root directory
        project_root = Path(__file__).parent.parent
        logs_dir = project_root / "logs"
        
        # Create logs directory
        os.makedirs(logs_dir, exist_ok=True)
        
        # Create timestamped log file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = logs_dir / f"research_{timestamp}.json"
        
        # Initialize log file with empty structure
        initial_data = {
            "events": [],
            "content": {
                "query": self.query,
                "sources": [],
                "report": ""
            }
        }
        
        with open(log_file, 'w') as f:
            json.dump(initial_data, f, indent=2)
            
        return log_file

    async def send_json(self, data: Dict[str, Any]) -> None:
        """Send JSON data and log it, with error handling."""
        try:
            # Append data to logs
            self.logs.append(data)
            
            # Log using logging
            self.logger.info(f"Log: {data}")
            
            # Send to websocket if available
            if self.websocket:
                await self.websocket.send_json(data)
                
            # Write to log file if available
            if hasattr(self, 'log_file'):
                self._append_to_log_file(data)
                
        except Exception as e:
            self.logger.error(f"Error logging data: {e}")

    def _append_to_log_file(self, data: Dict[str, Any]) -> None:
        """Append data to the JSON log file."""
        try:
            with open(self.log_file, 'r+') as f:
                log_data = json.load(f)
                log_data["events"].append({
                    "timestamp": datetime.now().isoformat(),
                    "data": data
                })
                f.seek(0)
                json.dump(log_data, f, indent=2)
                f.truncate()
        except Exception as e:
            self.logger.error(f"Error writing to log file: {e}")

    def clear_logs(self) -> None:
        """Clear the logs."""
        self.logs.clear()
        self.logger.info("Logs cleared.")