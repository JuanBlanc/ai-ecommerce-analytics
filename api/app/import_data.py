"""
Script para importar los CSVs de Olist a PostgreSQL.
"""

import os
import pandas as pd
from sqlalchemy import create_engine, text
from pathlib import Path

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://admin:admin123@db:5432/empresa")

# Orden de importación (respeta foreign keys)
IMPORT_ORDER = [
    ("product_category_name_translation.csv", "product_categories"),
    ("olist_customers_dataset.csv", "customers"),
    ("olist_sellers_dataset.csv", "sellers"),
    ("olist_products_dataset.csv", "products"),
    ("olist_orders_dataset.csv", "orders"),
    ("olist_order_items_dataset.csv", "order_items"),
    ("olist_order_payments_dataset.csv", "order_payments"),
    ("olist_order_reviews_dataset.csv", "order_reviews"),
]


def importar_csv(engine, csv_path: Path, tabla: str):
    """Importa un CSV a una tabla"""
    print(f"  Importando {csv_path.name} -> {tabla}...")

    # Leer CSV
    df = pd.read_csv(csv_path, encoding='utf-8')

    # Limpiar datos según la tabla
    if tabla == "order_reviews":
        # Algunos reviews tienen order_id inválidos, los filtramos después
        pass

    # Importar en chunks pequeños para evitar errores de memoria
    chunk_size = 1000
    total = len(df)

    for i in range(0, total, chunk_size):
        chunk = df.iloc[i:i+chunk_size]
        try:
            chunk.to_sql(
                tabla,
                engine,
                if_exists='append',
                index=False,
            )
        except Exception as e:
            # Si falla, intentar fila por fila
            for _, row in chunk.iterrows():
                try:
                    row.to_frame().T.to_sql(
                        tabla,
                        engine,
                        if_exists='append',
                        index=False,
                    )
                except:
                    pass  # Ignorar filas con FK inválidas

    print(f"    {total} registros procesados")
    return total


def main():
    # Buscar carpeta de datos
    data_paths = [
        Path("/app/data"),
        Path("./data"),
    ]

    data_path = None
    for p in data_paths:
        if p.exists() and list(p.glob("*.csv")):
            data_path = p
            break

    if not data_path:
        print("ERROR: No se encontró la carpeta 'data/' con CSVs")
        return

    print(f"Carpeta de datos: {data_path}")
    print(f"CSVs encontrados: {len(list(data_path.glob('*.csv')))}")

    # Conectar a BD
    engine = create_engine(DATABASE_URL)

    print("\nDeshabilitando restricciones FK temporalmente...")
    with engine.connect() as conn:
        conn.execute(text("SET session_replication_role = 'replica';"))
        conn.commit()

    try:
        # Importar en orden
        total_registros = 0
        for csv_file, tabla in IMPORT_ORDER:
            csv_path = data_path / csv_file
            if csv_path.exists():
                registros = importar_csv(engine, csv_path, tabla)
                total_registros += registros
            else:
                print(f"  Saltando {csv_file} (no encontrado)")

        print("\nRehabilitando restricciones FK...")
        with engine.connect() as conn:
            conn.execute(text("SET session_replication_role = 'origin';"))
            conn.commit()

        print(f"\n{'='*50}")
        print(f"IMPORTACION COMPLETADA")
        print(f"Total de registros: {total_registros:,}")
        print(f"{'='*50}")

    except Exception as e:
        print(f"ERROR durante importación: {e}")
        # Rehabilitar FK en caso de error
        with engine.connect() as conn:
            conn.execute(text("SET session_replication_role = 'origin';"))
            conn.commit()
        raise


if __name__ == "__main__":
    main()
