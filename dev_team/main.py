from dotenv import load_dotenv
from . import run_dev_team_flow
load_dotenv()

result = run_dev_team_flow(repo_url="https://github.com/assafelovic/gpt-researcher", query="Analyze the project structure")
print(result)