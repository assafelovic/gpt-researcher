from azure.storage.blob import BlobServiceClient
import os
import tempfile

class AzureDocumentLoader:
    def __init__(self, container_name, connection_string):
        self.client = BlobServiceClient.from_connection_string(connection_string)
        self.container = self.client.get_container_client(container_name)

    async def load(self):
        """Download all blobs to temp files and return their paths."""
        temp_dir = tempfile.mkdtemp()
        blobs = self.container.list_blobs()
        file_paths = []
        for blob in blobs:
            blob_client = self.container.get_blob_client(blob.name)
            local_path = os.path.join(temp_dir, blob.name)
            with open(local_path, "wb") as f:
                blob_data = blob_client.download_blob()
                f.write(blob_data.readall())
            file_paths.append(local_path)
        return file_paths  # Pass to existing DocumentLoader