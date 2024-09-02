import os
from github import Github
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import OpenAIEmbeddings

from langchain.text_splitter import CharacterTextSplitter
from langchain_core.documents import Document

class GithubAgent:
    def __init__(self, github_token, repo_name):
        self.github = Github(github_token)
        self.repo_name = repo_name
        self.repo = self.github.get_repo(self.repo_name)
        self.vector_store = None
        self.get_vector_store()  # Add this line

    async def fetch_repo_data(self, state=None):  # Add state parameter with default value None
        repo = self.github.get_repo(self.repo_name)
        contents = repo.get_contents("")
        directory_structure = self.log_directory_structure(contents)
        vector_store = await self.save_to_vector_store(contents)
        return {"github_data": directory_structure, 
                "vector_store": vector_store,
                "repo_name": self.repo_name
                }  # Return a dictionary with the result

    def log_directory_structure(self, contents, path=""):
        structure = []
        for content in contents:
            if content.type == "dir":
                structure.append(f"{path}{content.name}/")
                structure.extend(self.log_directory_structure(self.repo.get_contents(content.path), f"{path}{content.name}/"))
            else:
                structure.append(f"{path}{content.name}")
        return structure

    async def save_to_vector_store(self, contents):
        documents = []
        for content in contents:
            if content.type == "file":
                print(f"Processing {content.name}")
                print(content.decoded_content.decode())
                # Create a Document instance with the correct structure
                doc = Document(page_content=content.decoded_content.decode(), metadata={"source": content.name})
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