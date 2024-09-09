from dotenv import load_dotenv
import os
from dev_team.agents.github_agent import GithubAgent

load_dotenv()

def main():
    # Get GitHub token from environment variables
    github_token = os.getenv('GITHUB_TOKEN')
    
    # Initialize GithubAgent with the gpt-researcher repo
    github_agent = GithubAgent(github_token=github_token, repo_name="assafelovic/gpt-researcher")
    
    # Fetch repo data
    repo_structure = github_agent.fetch_repo_data()
    
    # Print the directory structure to verify
    print("Repository structure:")
    for item in repo_structure:
        print(item)
    
    # Verify that the vector store was created
    vector_store = github_agent.get_vector_store()
    if vector_store:
        print("Vector store created successfully")
    else:
        print("Failed to create vector store")

if __name__ == "__main__":
    main()