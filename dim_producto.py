"""
Pipeline de actualización de la dimensión Producto (esquema estrella).
Flujo ETL: extraer -> transformar -> cargar (SCD Tipo 1).
"""
import sqlite3
from datetime import datetime

import pandas as pd

DB_PATH = "dw_tienda.db"
CSV_PATH = "datos/productos.csv"

CREAR_TABLA = """
CREATE TABLE IF NOT EXISTS dim_producto (
    sk_producto         INTEGER PRIMARY KEY AUTOINCREMENT,  -- llave sustituta
    id_producto         INTEGER NOT NULL UNIQUE,            -- llave natural
    nombre              TEXT,
    categoria           TEXT,
    marca               TEXT,
    precio              REAL,
    fecha_actualizacion TEXT
)
"""


def extraer():
    """E: lee los datos crudos desde el CSV."""
    return pd.read_csv(CSV_PATH)


def transformar(df):
    """T: limpia y estandariza los datos."""
    df = df.drop_duplicates(subset="id_producto", keep="last")
    df = df.dropna(subset=["id_producto"])
    df["nombre"] = df["nombre"].str.strip().str.title()
    df["categoria"] = df["categoria"].fillna("Sin categoría").str.strip().str.title()
    df["marca"] = df["marca"].fillna("Sin marca").str.strip().str.title()
    df["precio"] = pd.to_numeric(df["precio"], errors="coerce").fillna(0.0)  # precio inválido -> 0
    return df


def cargar(df):
    """L: compara contra la dimensión y hace insert / update / nada."""
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute(CREAR_TABLA)

    existentes = {
        fila[0]: fila[1:]
        for fila in cur.execute(
            "SELECT id_producto, nombre, categoria, marca, precio FROM dim_producto"
        )
    }

    ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    nuevos = actualizados = sin_cambios = 0

    for f in df.to_dict("records"):
        clave = int(f["id_producto"])
        valores = (f["nombre"], f["categoria"], f["marca"], float(f["precio"]))

        if clave not in existentes:
            cur.execute(
                "INSERT INTO dim_producto (id_producto, nombre, categoria, marca, precio, fecha_actualizacion) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (clave, *valores, ahora),
            )
            nuevos += 1
        elif existentes[clave] != valores:
            cur.execute(
                "UPDATE dim_producto SET nombre=?, categoria=?, marca=?, precio=?, fecha_actualizacion=? "
                "WHERE id_producto=?",
                (*valores, ahora, clave),
            )
            actualizados += 1
        else:
            sin_cambios += 1

    con.commit()
    con.close()
    print(f"dim_producto -> nuevos: {nuevos} | actualizados: {actualizados} | sin cambios: {sin_cambios}")


def main():
    df = extraer()
    df = transformar(df)
    cargar(df)


if __name__ == "__main__":
    main()