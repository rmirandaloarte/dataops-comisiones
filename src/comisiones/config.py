"""Configuración del pipeline leída desde variables de entorno.

Nada sensible se guarda en el repositorio: las credenciales llegan por
variables de entorno (archivo .env en local, GitHub Secrets en CI/CD).
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass

try:  # python-dotenv es opcional
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # pragma: no cover
    pass

# Cadena de conexión pública y documentada del emulador Azurite.
AZURITE_CONNECTION_STRING = (
    "DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;"
    "AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/"
    "K1SZFPTOtr/KBHBeksoGMGw==;BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;"
)

_IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _ident(value: str, name: str) -> str:
    if not _IDENT.match(value):
        raise ValueError(f"Identificador SQL inválido en {name}: {value!r}")
    return value


@dataclass(frozen=True)
class Settings:
    environment: str
    # PostgreSQL (dmc.rrhh.empleado)
    pg_host: str
    pg_port: int
    pg_database: str
    pg_user: str
    pg_password: str
    pg_schema: str
    pg_table: str
    # Almacenamiento (Blob / Data Lake)
    storage_mode: str  # "blob" | "local"
    storage_connection_string: str
    local_datalake_dir: str
    raw_container: str
    curated_container: str
    csv_blob_name: str
    # Reglas de negocio
    join_type: str  # "inner" | "left"

    @property
    def csv_file_name(self) -> str:
        return self.csv_blob_name.rsplit("/", 1)[-1]


def _env(name: str, default: str) -> str:
    """Como os.getenv, pero trata el valor vacío como no definido (útil en CI)."""
    value = os.getenv(name)
    return value if value not in (None, "") else default


def get_settings(environment: str | None = None) -> Settings:
    env = (environment or _env("ENVIRONMENT", "dev")).lower()
    if env not in {"dev", "test", "prod"}:
        raise ValueError(f"ENVIRONMENT debe ser dev, test o prod (recibido: {env})")

    join_type = _env("JOIN_TYPE", "inner").lower()
    if join_type not in {"inner", "left"}:
        raise ValueError("JOIN_TYPE debe ser 'inner' o 'left'")

    storage_mode = _env("STORAGE_MODE", "blob").lower()
    if storage_mode not in {"blob", "local"}:
        raise ValueError("STORAGE_MODE debe ser 'blob' o 'local'")

    return Settings(
        environment=env,
        pg_host=_env("PG_HOST", "localhost"),
        pg_port=int(_env("PG_PORT", "5432")),
        pg_database=_env("PG_DATABASE", "dmc"),
        pg_user=_env("PG_USER", "postgres"),
        pg_password=_env("PG_PASSWORD", ""),
        pg_schema=_ident(_env("PG_SCHEMA", "rrhh"), "PG_SCHEMA"),
        pg_table=_ident(_env("PG_TABLE", "empleado"), "PG_TABLE"),
        storage_mode=storage_mode,
        storage_connection_string=_env(
            "AZURE_STORAGE_CONNECTION_STRING", AZURITE_CONNECTION_STRING
        ),
        local_datalake_dir=_env("LOCAL_DATALAKE_DIR", "./datalake"),
        raw_container=_env("RAW_CONTAINER", "raw"),
        curated_container=_env("CURATED_CONTAINER", "curated"),
        csv_blob_name=_env("CSV_BLOB_NAME", "comisiones/ComisionEmpleados_V1_202610.csv"),
        join_type=join_type,
    )
