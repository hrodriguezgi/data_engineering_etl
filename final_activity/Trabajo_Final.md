# Trabajo final - ETL Carpintería Pinocho

La empresa Carpintería Pinocho cuenta con 3 sucursales en Antioquia y necesita consolidar su información comercial en una única sábana de datos confiable para análisis posterior.

Cada sucursal administra la información en un formato distinto:

- La sucursal norte almacena la información en una base de datos DuckDB/SQLite. Allí se encuentran las tablas `clientes`, `productos` y `ventas`.
- La sucursal centro registra sus ventas en un archivo plano CSV, donde cada fila contiene información de la venta y del cliente asociado.
- La sucursal sur administra la información en un archivo Excel con dos hojas: `productos` y `ventas`.

El objetivo del trabajo es diseñar e implementar un proceso ETL que permita:

1. Extraer la información desde las tres fuentes.
2. Transformar y estandarizar los datos.
3. Identificar y tratar registros nulos, duplicados e inconsistentes.
4. Integrar la información en una sola sábana de datos.
5. Exportar la salida final en formato `parquet`.
6. Realizar una carga adicional de la sábana final a una base de datos SQL (DuckDB/SQLite).

La sábana final debe contener la siguiente información para cada venta:
- sucursal (norte, centro, sur)
- venta
- fecha (en formato YYYY-MM-DD)
- cliente
- producto
- cantidad
- precio unitario
- total de la venta

Durante el desarrollo deberán resolverse problemas de calidad de datos, tales como:
- valores nulos
- registros duplicados
- nombres de columnas distintos entre fuentes
- formatos diferentes de fecha
- inconsistencias en nombres de clientes o productos

La solución debe desarrollarse usando Pandas y DuckDB/SQLite, aplicando buenas prácticas de organización del proceso ETL.