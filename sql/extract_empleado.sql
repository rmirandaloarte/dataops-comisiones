-- Consulta de extracción usada por el pipeline (src/comisiones/extract.py)
-- Fuente: base dmc, esquema rrhh, tabla empleado  (dmc.rrhh.empleado)
SELECT empleado_id,
       nom_empleado,
       ape_empleado,
       cod_cargo,
       cod_departamento,
       mnt_salario,
       mnt_tope_comision
FROM rrhh.empleado;
