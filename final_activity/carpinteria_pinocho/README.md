# Carpinteria Pinocho - insumos del trabajo final

Este conjunto de datos sirve como base para el trabajo final del curso.

## Fuentes incluidas

- `sucursal_norte.duckdb`
  - tablas: `clientes`, `productos`, `ventas`
- `ventas_centro.csv`
- `sucursal_sur.xlsx`
  - hojas: `productos`, `ventas`

## Problemas de calidad intencionales

- nulos en campos criticos como `cantidad`, `cliente` o `valor_unitario`;
- duplicados exactos en ventas;
- diferencias de mayusculas/minusculas y espacios sobrantes;
- formatos mixtos de fecha;
- categorias inconsistentes;
- una referencia a producto inexistente en la sucursal sur.

## Script generador

Si necesitas regenerar los archivos:

```bash
python module_3_data_extraction/generate_carpinteria_pinocho_inputs.py
```
