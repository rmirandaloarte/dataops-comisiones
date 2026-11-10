"""Transformaciones: lectura del CSV de comisiones, join y salario_total."""

from __future__ import annotations

import io
import logging
import re
from datetime import datetime, timezone

import pandas as pd

log = logging.getLogger(__name__)


class DataQualityError(ValueError):
    """Se lanza cuando los datos no cumplen las reglas de calidad."""


def periodo_from_filename(file_name: str) -> str:
    """'ComisionEmpleados_V1_202610.csv' -> '202610'."""
    match = re.search(r"_(\d{6})\.csv$", file_name, flags=re.IGNORECASE)
    if not match:
        raise ValueError(f"No se encontró el periodo AAAAMM en el nombre: {file_name}")
    return match.group(1)


def parse_comisiones_csv(raw: bytes) -> pd.DataFrame:
    """Lee el CSV (separador ';', 'Nombre, Apellido' en una sola columna)."""
    for encoding in ("utf-8-sig", "latin-1"):
        try:
            text = raw.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    df = pd.read_csv(io.StringIO(text), sep=";", dtype=str, skip_blank_lines=True)
    df.columns = [c.strip() for c in df.columns]

    rename = {
        "empleado_id": "empleado_id",
        "Nombre y Apellido": "nombre_apellido_csv",
        "Comisión": "comision",
        "Comision": "comision",
    }
    missing = {"empleado_id", "comision"} - set(rename.get(c, c) for c in df.columns)
    if missing:
        raise DataQualityError(f"Columnas faltantes en el CSV: {sorted(missing)}")
    df = df.rename(columns=rename)
    df = df.dropna(how="all")

    df["empleado_id"] = pd.to_numeric(df["empleado_id"].str.strip(), errors="coerce")
    df["comision"] = pd.to_numeric(
        df["comision"].str.strip().str.replace(",", ".", regex=False), errors="coerce"
    )
    if "nombre_apellido_csv" in df.columns:
        partes = df["nombre_apellido_csv"].str.split(",", n=1, expand=True)
        df["nombre_csv"] = partes[0].str.strip()
        df["apellido_csv"] = partes[1].str.strip() if partes.shape[1] > 1 else None

    errores = []
    if df["empleado_id"].isna().any():
        errores.append("empleado_id nulo o no numérico")
    if df["comision"].isna().any():
        errores.append("comisión nula o no numérica")
    if (df["comision"] < 0).any():
        errores.append("comisión negativa")
    if df["empleado_id"].duplicated().any():
        dups = df.loc[df["empleado_id"].duplicated(), "empleado_id"].tolist()
        errores.append(f"empleado_id duplicado: {dups}")
    if errores:
        raise DataQualityError("CSV de comisiones inválido: " + "; ".join(errores))

    df["empleado_id"] = df["empleado_id"].astype("int64")
    log.info("CSV de comisiones leído: %d filas", len(df))
    return df


def validate_empleados(df: pd.DataFrame) -> pd.DataFrame:
    requeridas = {"empleado_id", "mnt_salario"}
    faltan = requeridas - set(df.columns)
    if faltan:
        raise DataQualityError(f"Columnas faltantes en empleado: {sorted(faltan)}")
    if df.empty:
        raise DataQualityError("La tabla empleado no devolvió filas")
    if df["empleado_id"].duplicated().any():
        raise DataQualityError("empleado_id duplicado en la tabla empleado")
    df = df.copy()
    df["empleado_id"] = df["empleado_id"].astype("int64")
    df["mnt_salario"] = pd.to_numeric(df["mnt_salario"], errors="coerce")
    if df["mnt_salario"].isna().any():
        raise DataQualityError("mnt_salario nulo o no numérico")
    if "mnt_tope_comision" in df.columns:
        df["mnt_tope_comision"] = pd.to_numeric(df["mnt_tope_comision"], errors="coerce")
    return df


def build_salario_total(
    empleados: pd.DataFrame,
    comisiones: pd.DataFrame,
    periodo: str,
    environment: str,
    join_type: str = "inner",
) -> tuple[pd.DataFrame, dict]:
    """Join por empleado_id y cálculo salario_total = salario + comisión."""
    empleados = validate_empleados(empleados)
    cols_csv = ["empleado_id", "comision"] + [
        c for c in ("nombre_csv", "apellido_csv") if c in comisiones.columns
    ]
    df = empleados.merge(comisiones[cols_csv], on="empleado_id", how=join_type)

    df["comision"] = df["comision"].fillna(0.0).astype("float64")
    df["salario_total"] = (df["mnt_salario"] + df["comision"]).round(2)
    if "mnt_tope_comision" in df.columns:
        df["excede_tope_comision"] = df["comision"] > df["mnt_tope_comision"]
    df["periodo"] = periodo
    df["ambiente"] = environment
    df["fecha_proceso"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    df = df.sort_values("empleado_id").reset_index(drop=True)

    ids_emp = set(empleados["empleado_id"])
    ids_csv = set(comisiones["empleado_id"])
    report = {
        "periodo": periodo,
        "ambiente": environment,
        "join_type": join_type,
        "filas_empleado": len(empleados),
        "filas_csv": len(comisiones),
        "filas_salida": len(df),
        "csv_sin_empleado": sorted(int(i) for i in ids_csv - ids_emp),
        "empleados_sin_comision": len(ids_emp - ids_csv),
        "total_salario": float(df["mnt_salario"].sum()),
        "total_comision": float(df["comision"].sum()),
        "total_salario_total": float(df["salario_total"].sum()),
        "empleados_exceden_tope": int(df.get("excede_tope_comision", pd.Series(dtype=bool)).sum()),
    }
    run_quality_checks(df, report)
    return df, report


def run_quality_checks(df: pd.DataFrame, report: dict) -> None:
    checks = {
        "salida_no_vacia": len(df) > 0,
        "empleado_id_unico": not df["empleado_id"].duplicated().any(),
        "salario_total_sin_nulos": not df["salario_total"].isna().any(),
        "salario_total_cuadra": bool(
            ((df["mnt_salario"] + df["comision"]).round(2) - df["salario_total"]).abs().max() < 0.01
        ),
        "comision_no_negativa": bool((df["comision"] >= 0).all()),
    }
    report["checks"] = checks
    fallidos = [k for k, ok in checks.items() if not ok]
    if fallidos:
        raise DataQualityError(f"Checks de calidad fallidos: {fallidos}")
    if report["csv_sin_empleado"]:
        log.warning(
            "IDs del CSV que no existen en empleado (se excluyen): %s",
            report["csv_sin_empleado"],
        )


def to_parquet_bytes(df: pd.DataFrame) -> bytes:
    buffer = io.BytesIO()
    df.to_parquet(buffer, index=False, engine="pyarrow")
    return buffer.getvalue()
