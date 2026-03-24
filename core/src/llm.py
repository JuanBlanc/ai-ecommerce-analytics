"""
Cliente LLM con soporte para:
- Gemini (API externa, opcional)
- Ollama (local): sqlcoder para SQL + llama3.1 para análisis
"""

import os
import json
import httpx

# Configuración
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434")
SQL_MODEL = os.getenv("SQL_MODEL", "sqlcoder:7b")
CHAT_MODEL = os.getenv("CHAT_MODEL", "llama3.1:8b")

# Determinar qué backend usar
USE_GEMINI = bool(GEMINI_API_KEY)

if USE_GEMINI:
    import google.generativeai as genai
    genai.configure(api_key=GEMINI_API_KEY)
    print(f"[LLM] Usando Gemini (API externa)")
else:
    print(f"[LLM] Usando Ollama local - SQL: {SQL_MODEL}, Chat: {CHAT_MODEL}")


# Esquema de la base de datos
DB_SCHEMA = """
Tablas de e-commerce (PostgreSQL):

1. customers (customer_id, customer_unique_id, customer_zip_code_prefix, customer_city, customer_state)
2. sellers (seller_id, seller_zip_code_prefix, seller_city, seller_state)
3. products (product_id, product_category_name, product_weight_g, product_length_cm, product_height_cm, product_width_cm)
4. product_categories (product_category_name, product_category_name_english)
5. orders (order_id, customer_id, order_status, order_purchase_timestamp, order_approved_at, order_delivered_carrier_date, order_delivered_customer_date, order_estimated_delivery_date)
6. order_items (order_id, order_item_id, product_id, seller_id, shipping_limit_date, price, freight_value)
7. order_payments (order_id, payment_sequential, payment_type, payment_installments, payment_value)
8. order_reviews (review_id, order_id, review_score, review_comment_title, review_comment_message, review_creation_date)

Estados de pedido: created, approved, invoiced, shipped, delivered, canceled
Métodos de pago: credit_card, boleto, voucher, debit_card
"""


def ollama_generate(model: str, prompt: str, timeout: float = 60.0) -> str:
    """Genera texto usando Ollama."""
    try:
        with httpx.Client(timeout=timeout) as client:
            response = client.post(
                f"{OLLAMA_URL}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,
                        "num_predict": 1000
                    }
                }
            )
            if response.status_code == 200:
                return response.json().get("response", "")
            else:
                print(f"[Ollama] Error: {response.status_code} - {response.text}")
                return ""
    except Exception as e:
        print(f"[Ollama] Error de conexión: {e}")
        return ""


def generar_sql_ollama(pregunta: str) -> dict:
    """Genera SQL usando sqlcoder (Ollama)."""
    prompt = f"""### Task
Generate a SQL query to answer the following question: `{pregunta}`

### Database Schema
{DB_SCHEMA}

### SQL
Only respond with the SQL query, no explanation. Use LIMIT 20.
"""

    response = ollama_generate(SQL_MODEL, prompt)

    if response:
        # Limpiar respuesta
        sql = response.strip()
        if "```" in sql:
            sql = sql.replace("```sql", "").replace("```", "").strip()

        # Validar que es SQL
        if sql.upper().startswith("SELECT"):
            if "LIMIT" not in sql.upper():
                sql += " LIMIT 20"
            return {"sql": sql}

    return {"sql": None}


def generar_sql_gemini(pregunta: str) -> dict:
    """Genera SQL usando Gemini."""
    try:
        model = genai.GenerativeModel('gemini-pro')

        prompt = f"""Genera SOLO una query SQL para PostgreSQL. Sin explicaciones.

{DB_SCHEMA}

Pregunta: {pregunta}

Responde SOLO con el SELECT (máximo 20 filas con LIMIT):"""

        response = model.generate_content(prompt)
        text = response.text.strip()

        # Limpiar
        if "```" in text:
            text = text.replace("```sql", "").replace("```", "").strip()

        if text.upper().startswith("SELECT"):
            if "LIMIT" not in text.upper():
                text += " LIMIT 20"
            return {"sql": text}

        return {"sql": None}
    except Exception as e:
        print(f"[Gemini] Error: {e}")
        return {"sql": None, "error": str(e)}


def analizar_ollama(pregunta: str, datos: list, columnas: list) -> dict:
    """Analiza resultados usando llama3.1 (Ollama)."""
    if not datos:
        return {
            "respuesta": "No se encontraron resultados.",
            "grafica": {"tipo": "table", "x": None, "y": None, "titulo": "Sin resultados"},
            "insights": []
        }

    datos_str = json.dumps(datos[:10], indent=2, default=str, ensure_ascii=False)

    prompt = f"""Analiza estos datos de e-commerce y responde en español.

Pregunta: {pregunta}
Columnas: {columnas}
Datos ({len(datos)} filas):
{datos_str}

Genera un JSON con:
1. "respuesta": explicación breve (2-3 frases)
2. "grafica": {{"tipo": "bar|line|pie|table", "x": "columna_x", "y": "columna_y", "titulo": "Título"}}
3. "insights": ["insight1", "insight2"]

Solo responde con el JSON:"""

    response = ollama_generate(CHAT_MODEL, prompt, timeout=90.0)

    try:
        # Intentar parsear JSON
        if "{" in response:
            start = response.find("{")
            end = response.rfind("}") + 1
            json_str = response[start:end]
            return json.loads(json_str)
    except:
        pass

    # Fallback
    return {
        "respuesta": response[:500] if response else f"Se encontraron {len(datos)} resultados.",
        "grafica": {
            "tipo": "bar" if len(columnas) >= 2 else "table",
            "x": columnas[0] if columnas else None,
            "y": columnas[1] if len(columnas) > 1 else None,
            "titulo": "Resultados"
        },
        "insights": [f"Total: {len(datos)} registros"]
    }


def analizar_gemini(pregunta: str, datos: list, columnas: list) -> dict:
    """Analiza resultados usando Gemini."""
    if not datos:
        return {
            "respuesta": "No se encontraron resultados.",
            "grafica": {"tipo": "table", "x": None, "y": None, "titulo": "Sin resultados"},
            "insights": []
        }

    try:
        model = genai.GenerativeModel('gemini-pro')
        datos_str = json.dumps(datos[:10], indent=2, default=str, ensure_ascii=False)

        prompt = f"""Analiza estos datos y responde en español con un JSON.

Pregunta: {pregunta}
Columnas: {columnas}
Datos: {datos_str}

JSON con: respuesta (2-3 frases), grafica (tipo/x/y/titulo), insights (lista de 2-3).
Solo el JSON:"""

        response = model.generate_content(prompt)
        text = response.text.strip()

        if "{" in text:
            start = text.find("{")
            end = text.rfind("}") + 1
            return json.loads(text[start:end])
    except Exception as e:
        print(f"[Gemini] Error análisis: {e}")

    # Fallback
    return {
        "respuesta": f"Se encontraron {len(datos)} resultados.",
        "grafica": {"tipo": "bar", "x": columnas[0] if columnas else None, "y": columnas[1] if len(columnas) > 1 else None, "titulo": "Resultados"},
        "insights": []
    }


# === FUNCIONES PÚBLICAS ===

def procesar_con_ia(pregunta: str) -> dict:
    """Genera SQL usando el backend configurado."""
    if USE_GEMINI:
        return generar_sql_gemini(pregunta)
    else:
        return generar_sql_ollama(pregunta)


def analizar_resultados(pregunta: str, datos: list, columnas: list) -> dict:
    """Analiza resultados usando el backend configurado."""
    if USE_GEMINI:
        return analizar_gemini(pregunta, datos, columnas)
    else:
        return analizar_ollama(pregunta, datos, columnas)
