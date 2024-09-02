import os
from github import Github
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings

class GithubAgent:
    def __init__(self, github_token, repo_name):
        self.github = Github(github_token)
        self.repo_name = repo_name
        self.vector_store = None

    def fetch_repo_data(self):
        repo = self.github.get_repo(self.repo_name)
        contents = repo.get_contents("")
        directory_structure = self.log_directory_structure(contents)
        self.save_to_vector_store(contents)
        return directory_structure

    def log_directory_structure(self, contents, path=""):
        structure = []
        for content in contents:
            if content.type == "dir":
                structure.append(f"{path}{content.name}/")
                structure.extend(self.log_directory_structure(self.repo.get_contents(content.path), f"{path}{content.name}/"))
            else:
                structure.append(f"{path}{content.name}")
        return structure

    def save_to_vector_store(self, contents):
        documents = []
        for content in contents:
            if content.type == "file":
                documents.append(content.decoded_content.decode())
        
        embeddings = OpenAIEmbeddings()
        self.vector_store = Chroma.from_texts(documents, embeddings)

    def get_vector_store(self):
        return self.vector_store