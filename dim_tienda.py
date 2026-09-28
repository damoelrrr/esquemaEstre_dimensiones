"""
Pipeline de actualización de la dimensión Tienda (esquema estrella).
Flujo ETL: extraer -> transformar -> cargar (SCD Tipo 1).
"""
import sqlite3
from datetime import datetime

import pandas as pd

DB_PATH = "dw_tienda.db"
CSV_PATH = "datos/tiendas.csv"

CREAR_TABLA = """
CREATE TABLE IF NOT EXISTS dim_tienda (
    sk_tienda           INTEGER PRIMARY KEY AUTOINCREMENT,  -- llave sustituta
    id_tienda           INTEGER NOT NULL UNIQUE,            -- llave natural
    nombre              TEXT,
    ciudad              TEXT,
    region              TEXT,
    fecha_actualizacion TEXT
)
"""


def extraer():
    """E: lee los datos crudos desde el CSV."""
    return pd.read_csv(CSV_PATH)


def transformar(df):
    """T: limpia y estandariza los datos."""
    df = df.drop_duplicates(subset="id_tienda", keep="last")
    df = df.dropna(subset=["id_tienda"])
    df["nombre"] = df["nombre"].str.strip().str.title()
    df["ciudad"] = df["ciudad"].str.strip().str.title()
    df["region"] = df["region"].fillna("Sin región").str.strip().str.title()
    return df


def cargar(df):
    """L: compara contra la dimensión y hace insert / update / nada."""
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute(CREAR_TABLA)

    existentes = {
        fila[0]: fila[1:]
        for fila in cur.execute("SELECT id_tienda, nombre, ciudad, region FROM dim_tienda")
    }

    ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    nuevos = actualizados = sin_cambios = 0

    for f in df.to_dict("records"):
        clave = int(f["id_tienda"])
        valores = (f["nombre"], f["ciudad"], f["region"])

        if clave not in existentes:
            cur.execute(
                "INSERT INTO dim_tienda (id_tienda, nombre, ciudad, region, fecha_actualizacion) "
                "VALUES (?, ?, ?, ?, ?)",
                (clave, *valores, ahora),
            )
            nuevos += 1
        elif existentes[clave] != valores:
            cur.execute(
                "UPDATE dim_tienda SET nombre=?, ciudad=?, region=?, fecha_actualizacion=? "
                "WHERE id_tienda=?",
                (*valores, ahora, clave),
            )
            actualizados += 1
        else:
            sin_cambios += 1

    con.commit()
    con.close()
    print(f"dim_tienda -> nuevos: {nuevos} | actualizados: {actualizados} | sin cambios: {sin_cambios}")


def main():
    df = extraer()
    df = transformar(df)
    cargar(df)


if __name__ == "__main__":
    main()