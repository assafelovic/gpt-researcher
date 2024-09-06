import os
from github import Github
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import OpenAIEmbeddings

from langchain.text_splitter import CharacterTextSplitter
from langchain_core.documents import Document
import base64

class GithubAgent:
    def __init__(self, github_token, repo_name, vector_store=None, branch_name=None):
        self.github = Github(github_token)
        self.repo_name = repo_name
        self.branch_name = branch_name
        self.repo = self.github.get_repo(self.repo_name)
        self.vector_store = vector_store
        self.get_vector_store()  # Add this line

    async def fetch_repo_data(self, state=None):
        repo = self.github.get_repo(self.repo_name)
        contents = repo.get_contents("", ref=self.branch_name)
        directory_structure = self.log_directory_structure(contents)
        # vector_store = await self.save_to_vector_store(contents)
        return {
            "github_data": directory_structure,
            # "vector_store": vector_store,
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

    async def save_to_vector_store(self, contents):
        documents = []
        for content in contents:
            if content.type == "file":
                print(f"Processing {content.name}")
                print(content.decoded_content.decode())
                file_content = self.repo.get_contents(content.path, ref=self.branch_name).decoded_content.decode()
                doc = Document(page_content=file_content, metadata={"source": content.name})
                documents.append(doc)
        
        text_splitter = CharacterTextSplitter(chunk_size=200, chunk_overlap=30, separator="\n")
        split_docs = text_splitter.split_documents(documents)

        embeddings = OpenAIEmbeddings()
        
        # Create a FAISS index from the documents
        self.vector_store = FAISS.from_documents(split_docs, embeddings)
        print("Index created successfully", self.vector_store)

        return self.vector_store
        
        # Save the index to disk (optional, but recommended for persistence)
        # index_path = os.path.join(os.getcwd(), "github_repo_index")
        # self.vector_store.save_local(index_path)

    def get_vector_store(self):
        return self.vector_store
    
    async def search_by_file_name(self, file_names):
        # Fetch relevant files from GitHub
        relevant_files = []
        for file_name in file_names:
            content = self.repo.get_contents(file_name, ref=self.branch_name)
            decoded_content = base64.b64decode(content.content).decode()
            relevant_files.append({
                "file_name": file_name,
                "content": decoded_content
            })

        return relevant_files
