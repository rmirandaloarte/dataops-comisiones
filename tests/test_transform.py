"""Pruebas unitarias de las transformaciones (no requieren BD ni Blob)."""

from pathlib import Path

import pandas as pd
import pytest

from comisiones.transform import (
    DataQualityError,
    build_salario_total,
    parse_comisiones_csv,
    periodo_from_filename,
    to_parquet_bytes,
)

DATA_CSV = Path(__file__).parents[1] / "data" / "ComisionEmpleados_V1_202610.csv"

CSV_OK = (
    "empleado_id;Nombre y Apellido;Comisión\r\n"
    "1;Juan, Pérez;9000\r\n"
    "2;María, Gómez;8250\r\n"
    "99;Fantasma, Nadie;100\r\n"
).encode("utf-8")


@pytest.fixture
def empleados():
    return pd.DataFrame(
        {
            "empleado_id": [1, 2, 3],
            "nom_empleado": ["Juan", "María", "Carlos"],
            "ape_empleado": ["Pérez", "Gómez", "Martínez"],
            "mnt_salario": [5000.0, 4000.0, 3000.0],
            "mnt_tope_comision": [10000.0, 8000.0, 9000.0],
        }
    )


def test_periodo_from_filename():
    assert periodo_from_filename("ComisionEmpleados_V1_202610.csv") == "202610"
    assert periodo_from_filename("ComisionEmpleados_V1_202608.csv") == "202608"
    with pytest.raises(ValueError):
        periodo_from_filename("comisiones.csv")


def test_parse_csv_separa_nombre_y_apellido():
    df = parse_comisiones_csv(CSV_OK)
    assert list(df["empleado_id"]) == [1, 2, 99]
    assert df.loc[0, "nombre_csv"] == "Juan"
    assert df.loc[0, "apellido_csv"] == "Pérez"
    assert df["comision"].sum() == 17350


def test_parse_csv_real_del_curso():
    df = parse_comisiones_csv(DATA_CSV.read_bytes())
    assert len(df) == 34
    assert df["empleado_id"].is_unique
    assert (df["comision"] > 0).all()


def test_parse_csv_detecta_duplicados():
    raw = b"empleado_id;Nombre y Apellido;Comision\n1;A, B;10\n1;A, B;20\n"
    with pytest.raises(DataQualityError, match="duplicado"):
        parse_comisiones_csv(raw)


def test_parse_csv_detecta_comision_invalida():
    raw = b"empleado_id;Nombre y Apellido;Comision\n1;A, B;abc\n"
    with pytest.raises(DataQualityError, match="comisi"):
        parse_comisiones_csv(raw)


def test_inner_join_calcula_salario_total(empleados):
    comisiones = parse_comisiones_csv(CSV_OK)
    df, report = build_salario_total(empleados, comisiones, "202610", "test", "inner")
    assert list(df["empleado_id"]) == [1, 2]
    assert list(df["salario_total"]) == [14000.0, 12250.0]
    assert report["csv_sin_empleado"] == [99]
    assert report["empleados_sin_comision"] == 1
    assert all(report["checks"].values())


def test_left_join_conserva_empleados_sin_comision(empleados):
    comisiones = parse_comisiones_csv(CSV_OK)
    df, _ = build_salario_total(empleados, comisiones, "202610", "test", "left")
    carlos = df[df["empleado_id"] == 3].iloc[0]
    assert carlos["comision"] == 0
    assert carlos["salario_total"] == 3000.0


def test_flag_excede_tope(empleados):
    comisiones = parse_comisiones_csv(CSV_OK)
    df, report = build_salario_total(empleados, comisiones, "202610", "test")
    # María: comisión 8250 > tope 8000
    assert bool(df.loc[df["empleado_id"] == 2, "excede_tope_comision"].iloc[0]) is True
    assert report["empleados_exceden_tope"] == 1


def test_empleados_vacio_falla():
    vacio = pd.DataFrame(columns=["empleado_id", "mnt_salario"])
    with pytest.raises(DataQualityError):
        build_salario_total(vacio, parse_comisiones_csv(CSV_OK), "202610", "test")


def test_parquet_roundtrip(empleados):
    df, _ = build_salario_total(empleados, parse_comisiones_csv(CSV_OK), "202610", "test")
    import io

    back = pd.read_parquet(io.BytesIO(to_parquet_bytes(df)))
    assert len(back) == len(df)
    assert "salario_total" in back.columns
