import asyncio
import os
from github import Github
from langchain_core.documents import Document
import base64
from .vector_agent import VectorAgent
import warnings
warnings.filterwarnings("ignore")
from langchain_community.document_loaders.generic import GenericLoader
from langchain_community.document_loaders.parsers import LanguageParser
from langchain_core.documents import Document
from langchain_text_splitters import Language
from langchain.text_splitter import RecursiveCharacterTextSplitter

class GithubAgent:
    def __init__(self, github_token, repo_name, vector_store=None, branch_name=None):
        self.github = Github(github_token)
        self.repo_name = repo_name
        self.branch_name = branch_name
        self.repo = self.github.get_repo(self.repo_name)
        self.vector_agent = VectorAgent()
        self.vector_store = vector_store
        self.get_vector_store()

    async def fetch_repo_data(self, state=None):
        repo = self.github.get_repo(self.repo_name)
        contents = self.repo.get_contents("", ref=self.branch_name)
        directory_structure = self.log_directory_structure(contents)
        vector_store = await self.save_to_vector_store(directory_structure)
        return {
            "github_data": directory_structure,
            "vector_store": vector_store,
            "github_agent": self,
            "repo_name": self.repo_name,
            "branch_name": self.branch_name
        }

    def log_directory_structure(self, contents, path=""):
        structure = []
        for content in contents:
            if content.type == "dir":
                structure.append(f"{path}{content.name}/")
                structure.extend(self.log_directory_structure(
                    self.repo.get_contents(content.path, ref=self.branch_name),
                    f"{path}{content.name}/"
                ))
            else:
                structure.append(f"{path}{content.name}")
        return structure

    async def save_to_vector_store(self, directory_structure):
        documents = []
        splitter = RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=30)

        for file_name in directory_structure:
            if not file_name.endswith('/'):
                try:
                    content = self.repo.get_contents(file_name, ref=self.branch_name)
                    decoded_content = base64.b64decode(content.content).decode(errors='ignore')
                    print("file_name", file_name)
                    print("content", decoded_content)

                    # Split each document into smaller chunks
                    chunks = splitter.split_text(decoded_content)
                    
                    # Extract metadata for each chunk
                    for chunk in chunks:
                        metadata = {
                            "source": file_name,
                            "title": file_name,
                            "extension": os.path.splitext(file_name)[1],
                            "file_path": file_name
                        }
                        document = Document(
                            page_content=chunk,
                            metadata=metadata
                        )
                        documents.append(document)

                except Exception as e:
                    print(f"Error saving to vector store: {e}")
                    return None

        self.vector_store = await self.vector_agent.save_to_vector_store(documents)
        return self.vector_store

    def get_vector_store(self):
        return self.vector_store

    async def search_by_file_name(self, file_names):
        relevant_files = []
        for file_name in file_names:
            content = self.repo.get_contents(file_name, ref=self.branch_name)
            decoded_content = base64.b64decode(content.content).decode(errors='ignore')
            relevant_files.append({
                "file_name": file_name,
                "content": decoded_content
            })
        return relevant_files