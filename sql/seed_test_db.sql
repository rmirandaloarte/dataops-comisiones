-- =====================================================================
-- DATOS SINTÉTICOS DE PRUEBA (no son los datos reales de la clase).
-- Replica la estructura de dmc.rrhh (departamento, cargo, empleado)
-- para el ambiente dev/CI usando un Postgres local o service container.
-- =====================================================================
CREATE SCHEMA IF NOT EXISTS rrhh;

DROP TABLE IF EXISTS rrhh.empleado;
DROP TABLE IF EXISTS rrhh.cargo;
DROP TABLE IF EXISTS rrhh.departamento;

CREATE TABLE rrhh.departamento (
    cod_departamento VARCHAR(10) PRIMARY KEY,
    des_departamento VARCHAR(100) NOT NULL
);

CREATE TABLE rrhh.cargo (
    cod_cargo VARCHAR(10) PRIMARY KEY,
    des_cargo VARCHAR(100) NOT NULL
);

CREATE TABLE rrhh.empleado (
    empleado_id       INTEGER PRIMARY KEY,
    tip_documento     VARCHAR(10),
    num_documento     VARCHAR(20),
    nom_empleado      VARCHAR(100),
    ape_empleado      VARCHAR(100),
    cod_cargo         VARCHAR(10) REFERENCES rrhh.cargo(cod_cargo),
    cod_departamento  VARCHAR(10) REFERENCES rrhh.departamento(cod_departamento),
    mnt_salario       NUMERIC(12,2) NOT NULL,
    mnt_tope_comision NUMERIC(12,2)
);

INSERT INTO rrhh.departamento VALUES ('D01','Ventas'),('D02','Operaciones'),('D03','Finanzas');
INSERT INTO rrhh.cargo VALUES ('C01','Analista'),('C02','Ejecutivo'),('C03','Supervisor');

INSERT INTO rrhh.empleado
(empleado_id, tip_documento, num_documento, nom_empleado, ape_empleado, cod_cargo, cod_departamento, mnt_salario, mnt_tope_comision)
VALUES
(1, 'DNI', '40000001', 'Juan', 'Pérez', 'C01', 'D03', 8000.00, 9000.00),
(2, 'DNI', '40000002', 'María', 'Gómez', 'C01', 'D01', 5000.00, 10000.00),
(3, 'DNI', '40000003', 'Carlos', 'Martínez', 'C03', 'D03', 8750.00, 9000.00),
(4, 'DNI', '40000004', 'Ana', 'López', 'C03', 'D02', 7250.00, 9000.00),
(5, 'DNI', '40000005', 'Pedro', 'Ramírez', 'C01', 'D01', 3250.00, 9000.00),
(6, 'DNI', '40000006', 'Lucía', 'Castro', 'C03', 'D01', 4750.00, 9000.00),
(7, 'DNI', '40000007', 'Jorge', 'Flores', 'C01', 'D02', 8500.00, 12000.00),
(8, 'DNI', '40000008', 'Rosa', 'Quispe', 'C01', 'D01', 7500.00, 11000.00),
(9, 'DNI', '40000009', 'Miguel', 'Martínez', 'C02', 'D02', 8500.00, 12000.00),
(10, 'DNI', '40000010', 'Isabella', 'López', 'C02', 'D01', 4000.00, 10000.00),
(11, 'DNI', '40000011', 'Daniel', 'Gómez', 'C01', 'D02', 3500.00, 12000.00),
(12, 'DNI', '40000012', 'Camila', 'Hernández', 'C01', 'D03', 5750.00, 11000.00),
(13, 'DNI', '40000013', 'Samuel', 'Torres', 'C02', 'D01', 6500.00, 9000.00),
(14, 'DNI', '40000014', 'Valeria', 'Rodríguez', 'C03', 'D03', 7250.00, 11000.00),
(15, 'DNI', '40000015', 'Benjamín', 'Pérez', 'C03', 'D01', 5750.00, 10000.00),
(16, 'DNI', '40000016', 'Luciana', 'García', 'C02', 'D01', 3250.00, 10000.00),
(17, 'DNI', '40000017', 'Martín', 'Díaz', 'C02', 'D02', 4750.00, 9000.00),
(18, 'DNI', '40000018', 'Juliana', 'Martínez', 'C01', 'D02', 6500.00, 11000.00),
(19, 'DNI', '40000019', 'Diego', 'Herrera', 'C03', 'D02', 5750.00, 10000.00),
(20, 'DNI', '40000020', 'Emilia', 'Sánchez', 'C03', 'D03', 8500.00, 9000.00),
(21, 'DNI', '40000021', 'Sebastián', 'Fernández', 'C01', 'D02', 4250.00, 10000.00),
(22, 'DNI', '40000022', 'Isaac', 'Luna', 'C03', 'D03', 6000.00, 11000.00),
(23, 'DNI', '40000023', 'Amanda', 'Gutierrez', 'C03', 'D02', 7250.00, 10000.00),
(24, 'DNI', '40000024', 'Oliver', 'Jiménez', 'C01', 'D01', 9000.00, 9000.00),
(25, 'DNI', '40000025', 'Paula', 'Romero', 'C02', 'D01', 5500.00, 12000.00),
(26, 'DNI', '40000026', 'Joaquín', 'Núñez', 'C01', 'D03', 4500.00, 11000.00),
(27, 'DNI', '40000027', 'Bianca', 'Silva', 'C03', 'D02', 6750.00, 12000.00),
(28, 'DNI', '40000028', 'Thiago', 'Hernández', 'C01', 'D01', 4000.00, 11000.00),
(29, 'DNI', '40000029', 'Ana Clara', 'Rojas', 'C03', 'D03', 8750.00, 11000.00),
(30, 'DNI', '40000030', 'Eduardo', 'Vargas', 'C02', 'D01', 6250.00, 12000.00),
(31, 'DNI', '40000031', 'Renata', 'Martínez', 'C01', 'D01', 4000.00, 12000.00),
(32, 'DNI', '40000032', 'Leonardo', 'López', 'C03', 'D01', 3750.00, 10000.00),
(33, 'DNI', '40000033', 'Laura', 'Herrera', 'C03', 'D01', 8250.00, 12000.00),
(34, 'DNI', '40000034', 'Iker', 'García', 'C03', 'D02', 6000.00, 12000.00),
(35, 'DNI', '40000035', 'Mariana', 'Díaz', 'C03', 'D01', 7000.00, 11000.00),
(36, 'DNI', '40000036', 'Max', 'Romero', 'C03', 'D03', 8250.00, 9000.00),
(37, 'DNI', '40000037', 'Aitana', 'Pérez', 'C03', 'D02', 9000.00, 11000.00),
(38, 'DNI', '40000038', 'Hugo', 'Salas', 'C02', 'D01', 3750.00, 11000.00),
(39, 'DNI', '40000039', 'Elena', 'Ríos', 'C03', 'D03', 6500.00, 9000.00),
(40, 'DNI', '40000040', 'Tomás', 'Vega', 'C03', 'D01', 5000.00, 10000.00);
