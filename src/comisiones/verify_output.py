"""Smoke test post-despliegue: lee el Parquet publicado y valida su contenido.

Uso:
    python -m comisiones.verify_output --env prod
"""

from __future__ import annotations

import argparse
import io
import logging
import sys
from pathlib import Path

import pandas as pd

from .config import get_settings
from .pipeline import output_paths
from .storage import get_storage
from .transform import periodo_from_filename

REQUIRED = {"empleado_id", "mnt_salario", "comision", "salario_total", "periodo"}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--env", choices=["dev", "test", "prod"], default=None)
    parser.add_argument("--min-rows", type=int, default=1)
    parser.add_argument("--download-dir", help="Guardar copia local del Parquet (evidencia)")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
    log = logging.getLogger("verify")

    settings = get_settings(args.env)
    storage = get_storage(settings)
    periodo = periodo_from_filename(settings.csv_file_name)
    parquet_path, _ = output_paths(settings, periodo)

    if not storage.exists(settings.curated_container, parquet_path):
        log.error("No existe el Parquet esperado: %s/%s", settings.curated_container, parquet_path)
        return 1
    data = storage.read_bytes(settings.curated_container, parquet_path)
    df = pd.read_parquet(io.BytesIO(data))
    if args.download_dir:
        out = Path(args.download_dir)
        out.mkdir(parents=True, exist_ok=True)
        (out / Path(parquet_path).name).write_bytes(data)
        df.to_csv(out / "salario_total_empleados_preview.csv", index=False)

    errores = []
    if len(df) < args.min_rows:
        errores.append(f"filas={len(df)} < {args.min_rows}")
    faltan = REQUIRED - set(df.columns)
    if faltan:
        errores.append(f"columnas faltantes {sorted(faltan)}")
    elif ((df["mnt_salario"] + df["comision"] - df["salario_total"]).abs() > 0.01).any():
        errores.append("salario_total no cuadra")
    if errores:
        log.error("Smoke test FALLÓ: %s", errores)
        return 1

    log.info("Smoke test OK: %d filas, periodo %s", len(df), periodo)
    print(df.head(10).to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
