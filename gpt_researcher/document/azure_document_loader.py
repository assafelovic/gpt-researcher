from azure.storage.blob import BlobServiceClient
import tempfile
from pathlib import Path, PurePosixPath


class AzureDocumentLoader:
    def __init__(self, container_name, connection_string):
        self.client = BlobServiceClient.from_connection_string(connection_string)
        self.container = self.client.get_container_client(container_name)

    async def load(self):
        """Download all blobs to temp files and return their paths."""
        temp_dir = Path(tempfile.mkdtemp()).resolve()
        blobs = self.container.list_blobs()
        file_paths = []
        for blob in blobs:
            blob_client = self.container.get_blob_client(blob.name)
            local_path = self._get_blob_path(temp_dir, blob.name)
            local_path.parent.mkdir(parents=True, exist_ok=True)
            with open(local_path, "wb") as f:
                blob_data = blob_client.download_blob()
                f.write(blob_data.readall())
            file_paths.append(str(local_path))
        return file_paths  # Pass to existing DocumentLoader

    @staticmethod
    def _get_blob_path(temp_dir: Path, blob_name: str) -> Path:
        """Return a safe local path for an Azure blob name."""
        blob_path = PurePosixPath(blob_name.replace("\\", "/"))
        if blob_path.is_absolute() or ".." in blob_path.parts:
            raise ValueError(f"Unsafe blob name: {blob_name}")

        local_path = (temp_dir / Path(*blob_path.parts)).resolve()
        if temp_dir != local_path and temp_dir not in local_path.parents:
            raise ValueError(f"Unsafe blob name: {blob_name}")

        return local_path
