from __future__ import annotations

import tempfile

from pathlib import Path
from typing import TYPE_CHECKING

from azure.storage.blob import BlobClient, BlobProperties, BlobServiceClient

if TYPE_CHECKING:
    from azure.storage.blob._container_client import ContainerClient


class AzureDocumentLoader:
    def __init__(
        self,
        container_name: str,
        connection_string: str,
    ):
        self.client: BlobServiceClient = BlobServiceClient.from_connection_string(connection_string)
        self.container: ContainerClient = self.client.get_container_client(container_name)

    async def load(self) -> list[str]:
        """Download all blobs to temp files and return their paths."""
        temp_dir: str = tempfile.mkdtemp()
        blobs: list[BlobProperties] = list(self.container.list_blobs())
        file_paths: list[str] = []
        for blob in blobs:
            blob_client: BlobClient = self.container.get_blob_client(blob.name)
            local_path: Path = Path(temp_dir, blob.name)
            local_path.write_bytes(blob_client.download_blob().readall())
            file_paths.append(str(local_path))
        return file_paths  # Pass to existing DocumentLoader
