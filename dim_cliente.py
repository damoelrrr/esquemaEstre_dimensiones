"""
Pipeline de actualización de la dimensión Cliente (esquema estrella).
Flujo ETL: extraer -> transformar -> cargar (SCD Tipo 1: se sobrescribe el valor viejo).
"""
import sqlite3
from datetime import datetime

import pandas as pd

DB_PATH = "dw_tienda.db"            # base de datos destino (se abre en DBeaver)
CSV_PATH = "datos/clientes.csv"     # fuente de datos

CREAR_TABLA = """
CREATE TABLE IF NOT EXISTS dim_cliente (
    sk_cliente          INTEGER PRIMARY KEY AUTOINCREMENT,  -- llave sustituta
    id_cliente          INTEGER NOT NULL UNIQUE,            -- llave natural (del sistema origen)
    nombre              TEXT,
    ciudad              TEXT,
    tipo_cliente        TEXT,
    fecha_actualizacion TEXT
)
"""


def extraer():
    """E: lee los datos crudos desde el CSV."""
    return pd.read_csv(CSV_PATH)


def transformar(df):
    """T: limpia y estandariza los datos."""
    df = df.drop_duplicates(subset="id_cliente", keep="last")  # sin llaves repetidas
    df = df.dropna(subset=["id_cliente"])                      # la llave no puede ser nula
    df["nombre"] = df["nombre"].str.strip().str.title()        # "  juan perez " -> "Juan Perez"
    df["ciudad"] = df["ciudad"].str.strip().str.title()
    df["tipo_cliente"] = df["tipo_cliente"].fillna("Sin clasificar")
    return df


def cargar(df):
    """L: compara contra la dimensión y hace insert / update / nada."""
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute(CREAR_TABLA)

    # Lo que ya existe en la dimensión, indexado por llave natural
    existentes = {
        fila[0]: fila[1:]
        for fila in cur.execute(
            "SELECT id_cliente, nombre, ciudad, tipo_cliente FROM dim_cliente"
        )
    }

    ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    nuevos = actualizados = sin_cambios = 0

    for f in df.to_dict("records"):
        clave = int(f["id_cliente"])
        valores = (f["nombre"], f["ciudad"], f["tipo_cliente"])

        if clave not in existentes:                     # registro NUEVO
            cur.execute(
                "INSERT INTO dim_cliente (id_cliente, nombre, ciudad, tipo_cliente, fecha_actualizacion) "
                "VALUES (?, ?, ?, ?, ?)",
                (clave, *valores, ahora),
            )
            nuevos += 1
        elif existentes[clave] != valores:              # registro CAMBIÓ
            cur.execute(
                "UPDATE dim_cliente SET nombre=?, ciudad=?, tipo_cliente=?, fecha_actualizacion=? "
                "WHERE id_cliente=?",
                (*valores, ahora, clave),
            )
            actualizados += 1
        else:                                           # sin cambios
            sin_cambios += 1

    con.commit()
    con.close()
    print(f"dim_cliente -> nuevos: {nuevos} | actualizados: {actualizados} | sin cambios: {sin_cambios}")


def main():
    df = extraer()
    df = transformar(df)
    cargar(df)


if __name__ == "__main__":
    main()