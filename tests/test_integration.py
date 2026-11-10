"""Prueba de integración end-to-end: Postgres + Blob (Azurite) -> Parquet.

Se ejecuta solo si RUN_INTEGRATION=1 (en CI se levanta Postgres con datos
sintéticos y Azurite como service containers).
"""

import io
import os
from pathlib import Path

import pandas as pd
import pytest

pytestmark = pytest.mark.skipif(os.getenv("RUN_INTEGRATION") != "1", reason="RUN_INTEGRATION != 1")

DATA_CSV = Path(__file__).parents[1] / "data" / "ComisionEmpleados_V1_202610.csv"


def test_pipeline_end_to_end():
    from comisiones.config import get_settings
    from comisiones.pipeline import output_paths, run
    from comisiones.storage import get_storage

    settings = get_settings("test")
    storage = get_storage(settings)
    storage.write_bytes(settings.raw_container, settings.csv_blob_name, DATA_CSV.read_bytes())

    report = run("test")
    assert report["filas_salida"] > 0
    assert all(report["checks"].values())

    parquet_path, report_path = output_paths(settings, "202610")
    df = pd.read_parquet(io.BytesIO(storage.read_bytes(settings.curated_container, parquet_path)))
    assert len(df) == report["filas_salida"]
    assert ((df["mnt_salario"] + df["comision"] - df["salario_total"]).abs() < 0.01).all()
    assert storage.exists(settings.curated_container, report_path)
