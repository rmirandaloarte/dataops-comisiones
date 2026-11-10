"""Extracción de la tabla dmc.rrhh.empleado desde PostgreSQL."""

from __future__ import annotations

import logging

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

log = logging.getLogger(__name__)

EMPLEADO_COLUMNS = [
    "empleado_id",
    "nom_empleado",
    "ape_empleado",
    "cod_cargo",
    "cod_departamento",
    "mnt_salario",
    "mnt_tope_comision",
]


def build_engine(settings):
    # URL.create escapa correctamente contraseñas con caracteres especiales (! % ^ * ...)
    url = URL.create(
        "postgresql+psycopg2",
        username=settings.pg_user,
        password=settings.pg_password,
        host=settings.pg_host,
        port=settings.pg_port,
        database=settings.pg_database,
    )
    return create_engine(url, pool_pre_ping=True, connect_args={"connect_timeout": 15})


def extract_empleados(settings, engine=None) -> pd.DataFrame:
    engine = engine or build_engine(settings)
    # schema y tabla ya fueron validados como identificadores en config.py
    query = text(
        f"SELECT {', '.join(EMPLEADO_COLUMNS)} FROM {settings.pg_schema}.{settings.pg_table}"
    )
    log.info(
        "Extrayendo %s.%s.%s desde %s",
        settings.pg_database,
        settings.pg_schema,
        settings.pg_table,
        settings.pg_host,
    )
    with engine.connect() as conn:
        df = pd.read_sql(query, conn)
    log.info("Empleados extraídos: %d filas", len(df))
    return df
