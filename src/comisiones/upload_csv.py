"""Sube el CSV de comisiones al contenedor raw (zona de aterrizaje del Data Lake).

Uso:
    python -m comisiones.upload_csv data/ComisionEmpleados_V1_202610.csv
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from .config import get_settings
from .storage import get_storage


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_path")
    parser.add_argument("--env", choices=["dev", "test", "prod"], default=None)
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")

    settings = get_settings(args.env)
    data = Path(args.csv_path).read_bytes()
    uri = get_storage(settings).write_bytes(settings.raw_container, settings.csv_blob_name, data)
    logging.info("CSV cargado en %s", uri)
    return 0


if __name__ == "__main__":
    sys.exit(main())
