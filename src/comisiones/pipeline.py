"""Orquestador del flujo: Postgres + CSV (Blob) -> join -> Parquet (Data Lake).

Uso:
    python -m comisiones.pipeline --env dev
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time

from .config import get_settings
from .extract import extract_empleados
from .storage import get_storage
from .transform import (
    build_salario_total,
    parse_comisiones_csv,
    periodo_from_filename,
    to_parquet_bytes,
)

log = logging.getLogger("comisiones")


def output_paths(settings, periodo: str) -> tuple[str, str]:
    base = f"salario_total/periodo={periodo}"
    return f"{base}/salario_total_empleados.parquet", f"{base}/_quality_report.json"


def run(environment: str | None = None, empleados_df=None) -> dict:
    t0 = time.time()
    settings = get_settings(environment)
    log.info("=== Pipeline comisiones | ambiente=%s ===", settings.environment)
    storage = get_storage(settings)

    # 1. Extract: PostgreSQL
    empleados = empleados_df if empleados_df is not None else extract_empleados(settings)

    # 2. Extract: CSV desde Blob Storage (contenedor raw)
    raw = storage.read_bytes(settings.raw_container, settings.csv_blob_name)
    comisiones = parse_comisiones_csv(raw)
    periodo = periodo_from_filename(settings.csv_file_name)

    # 3. Transform: join + salario_total + checks de calidad
    df, report = build_salario_total(
        empleados, comisiones, periodo, settings.environment, settings.join_type
    )

    # 4. Load: Parquet en el Data Lake (contenedor curated)
    parquet_path, report_path = output_paths(settings, periodo)
    report["salida_parquet"] = storage.write_bytes(
        settings.curated_container, parquet_path, to_parquet_bytes(df)
    )
    report["duracion_segundos"] = round(time.time() - t0, 2)
    storage.write_bytes(
        settings.curated_container,
        report_path,
        json.dumps(report, ensure_ascii=False, indent=2).encode("utf-8"),
    )
    log.info("Resumen: %s", json.dumps(report, ensure_ascii=False))
    log.info("=== Pipeline OK en %.2fs ===", report["duracion_segundos"])
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Pipeline de comisiones DataOps")
    parser.add_argument("--env", choices=["dev", "test", "prod"], default=None)
    parser.add_argument("--report-file", help="Guardar el reporte JSON en esta ruta local")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    try:
        report = run(args.env)
    except Exception:  # noqa: BLE001
        log.exception("El pipeline falló")
        return 1
    if args.report_file:
        with open(args.report_file, "w", encoding="utf-8") as fh:
            json.dump(report, fh, ensure_ascii=False, indent=2)
    return 0


if __name__ == "__main__":
    sys.exit(main())
