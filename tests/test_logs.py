import os
from pathlib import Path
import sys

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from backend.server.server_utils import CustomLogsHandler

def test_logs_creation():
    # Print current working directory
    print(f"Current working directory: {os.getcwd()}")
    
    # Print project root
    print(f"Project root: {project_root}")
    
    # Try to create logs directory directly
    logs_dir = project_root / "logs"
    print(f"Attempting to create logs directory at: {logs_dir}")
    
    try:
        # Create directory with full permissions
        os.makedirs(logs_dir, mode=0o777, exist_ok=True)
        print(f"✓ Created directory: {logs_dir}")
        
        # Test file creation
        test_file = logs_dir / "test.txt"
        with open(test_file, 'w') as f:
            f.write("Test log entry")
        print(f"✓ Created test file: {test_file}")
        
        # Initialize the handler
        handler = CustomLogsHandler()
        print("✓ CustomLogsHandler initialized")
        
        # Test JSON logging
        handler.logs.append({"test": "message"})
        print("✓ Added test log entry")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print(f"Error type: {type(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    test_logs_creation() 