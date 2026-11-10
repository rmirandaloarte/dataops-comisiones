"""Acceso al Data Lake: Azure Blob Storage (o Azurite) y modo local."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Protocol

log = logging.getLogger(__name__)
# El SDK de Azure registra cada request HTTP en INFO; lo silenciamos.
logging.getLogger("azure").setLevel(logging.WARNING)


class Storage(Protocol):
    def read_bytes(self, container: str, path: str) -> bytes: ...
    def write_bytes(self, container: str, path: str, data: bytes) -> str: ...
    def exists(self, container: str, path: str) -> bool: ...


class BlobStorage:
    """Azure Blob Storage / ADLS Gen2. Funciona igual con Azurite."""

    def __init__(self, connection_string: str):
        from azure.storage.blob import BlobServiceClient

        self.client = BlobServiceClient.from_connection_string(connection_string)

    def _container(self, name: str):
        container = self.client.get_container_client(name)
        if not container.exists():
            log.info("Creando contenedor '%s'", name)
            container.create_container()
        return container

    def read_bytes(self, container: str, path: str) -> bytes:
        log.info("Leyendo blob %s/%s", container, path)
        return self._container(container).download_blob(path).readall()

    def write_bytes(self, container: str, path: str, data: bytes) -> str:
        self._container(container).upload_blob(path, data, overwrite=True)
        uri = f"{self.client.url.rstrip('/')}/{container}/{path}"
        log.info("Blob escrito: %s (%d bytes)", uri, len(data))
        return uri

    def exists(self, container: str, path: str) -> bool:
        return self._container(container).get_blob_client(path).exists()


class LocalStorage:
    """Simula el Data Lake en una carpeta local (sin Docker ni Azure)."""

    def __init__(self, root: str):
        self.root = Path(root)

    def _path(self, container: str, path: str) -> Path:
        return self.root / container / path

    def read_bytes(self, container: str, path: str) -> bytes:
        return self._path(container, path).read_bytes()

    def write_bytes(self, container: str, path: str, data: bytes) -> str:
        target = self._path(container, path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        log.info("Archivo escrito: %s (%d bytes)", target, len(data))
        return str(target)

    def exists(self, container: str, path: str) -> bool:
        return self._path(container, path).exists()


def get_storage(settings) -> Storage:
    if settings.storage_mode == "local":
        return LocalStorage(settings.local_datalake_dir)
    return BlobStorage(settings.storage_connection_string)
