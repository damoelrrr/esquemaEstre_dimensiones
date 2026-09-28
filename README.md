# Pipeline de dimensiones – Esquema estrella

Pipeline ETL que actualiza las dimensiones **Cliente**, **Tienda** y **Producto** en SQLite (`dw_tienda.db`).

## Estructura
- `dim_cliente.py`, `dim_tienda.py`, `dim_producto.py`: un script independiente por dimensión.
- `datos/`: CSV de origen.

## Cómo ejecutar
```
pip install -r requirements.txt
python dim_cliente.py
python dim_tienda.py
python dim_producto.py
```
Luego abrir `dw_tienda.db` en DBeaver (Nueva conexión -> SQLite).

## Lógica
1. **Extract:** lee el CSV.
2. **Transform:** elimina duplicados y nulos en la llave, estandariza texto, rellena vacíos.
3. **Load (SCD Tipo 1):** inserta registros nuevos, actualiza los que cambiaron y omite los iguales.