#!/bin/bash
set -e

echo "=== Iniciando API Olist ==="

# Esperar a PostgreSQL
echo "Esperando a PostgreSQL..."
sleep 3

# Verificar si hay datos
echo "Verificando base de datos..."
ROWS=$(python -c "
from sqlalchemy import create_engine, text
import os
engine = create_engine(os.getenv('DATABASE_URL'))
with engine.connect() as conn:
    result = conn.execute(text('SELECT COUNT(*) FROM orders')).scalar()
    print(result)
" 2>/dev/null || echo "0")

echo "Registros en orders: $ROWS"

if [ "$ROWS" = "0" ] || [ -z "$ROWS" ]; then
    echo ""
    echo "=== Base de datos vacia - Importando CSVs ==="
    python -m app.import_data || echo "Advertencia: Algunos registros pueden haber fallado"
    echo "=== Importacion finalizada ==="
    echo ""
else
    echo "Base de datos ya tiene datos. Saltando importacion."
fi

echo "=== Iniciando servidor FastAPI ==="
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
