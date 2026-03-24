"""
Cliente LLM con soporte para:
- sqlcoder via Ollama (SQL gratis, opcional)
- Claude (API Anthropic)
- Gemini (API Google)

Prioridad SQL: Ollama > Claude > Gemini
Prioridad Analisis: Claude > Gemini
"""

import os
import json
import logging
import httpx

logger = logging.getLogger(__name__)


# === CONFIGURACION ===

class Config:
    """Configuracion centralizada del LLM."""
    SQL_LIMIT = 20
    MAX_TOKENS_SQL = 500
    MAX_TOKENS_ANALYSIS = 1000
    TEMPERATURE = 0.1

    CLAUDE_MODEL = "claude-haiku-4-5-20251001"
    GEMINI_MODEL = "gemini-pro"
    OLLAMA_MODEL = "sqlcoder:7b"
    OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434")


# Variables de entorno
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "").strip()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
USE_OLLAMA_ENV = os.getenv("USE_OLLAMA", "false").lower() in ("true", "1", "yes")

# Flags de disponibilidad
USE_CLAUDE = bool(ANTHROPIC_API_KEY)
USE_GEMINI = bool(GEMINI_API_KEY)
OLLAMA_AVAILABLE = False


# === ESQUEMA DE BASE DE DATOS ===

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
Metodos de pago: credit_card, boleto, voucher, debit_card
"""


# === FUNCIONES AUXILIARES ===

def _limpiar_sql(text: str) -> str:
    """Limpia markdown y espacios de respuesta SQL."""
    if "```" in text:
        text = text.replace("```sql", "").replace("```", "")
    return text.strip()


def _asegurar_limit(sql: str) -> str:
    """Agrega LIMIT si no existe en el SQL."""
    if sql and "LIMIT" not in sql.upper():
        sql += f" LIMIT {Config.SQL_LIMIT}"
    return sql


def _validar_sql(text: str) -> str | None:
    """Valida y limpia respuesta SQL. Retorna None si invalido."""
    text = _limpiar_sql(text)
    if text.upper().startswith("SELECT"):
        return _asegurar_limit(text)
    return None


def _extraer_json(text: str) -> dict | None:
    """Extrae objeto JSON de texto con contenido extra."""
    if "{" in text:
        start = text.find("{")
        end = text.rfind("}") + 1
        try:
            return json.loads(text[start:end])
        except json.JSONDecodeError:
            return None
    return None


def _respuesta_vacia() -> dict:
    """Respuesta estandar cuando no hay datos."""
    return {
        "respuesta": "No se encontraron resultados.",
        "grafica": {"tipo": "table", "x": None, "y": None, "titulo": "Sin resultados"},
        "insights": []
    }


def _respuesta_fallback(datos: list, columnas: list) -> dict:
    """Respuesta fallback cuando falla el analisis."""
    return {
        "respuesta": f"Se encontraron {len(datos)} resultados.",
        "grafica": {
            "tipo": "bar",
            "x": columnas[0] if columnas else None,
            "y": columnas[1] if len(columnas) > 1 else None,
            "titulo": "Resultados"
        },
        "insights": []
    }


# === INICIALIZACION ===

def check_ollama() -> bool:
    """Verifica si Ollama esta disponible y tiene sqlcoder."""
    global OLLAMA_AVAILABLE
    if not USE_OLLAMA_ENV:
        return False
    try:
        with httpx.Client(timeout=2.0) as http_client:
            response = http_client.get(f"{Config.OLLAMA_URL}/api/tags")
            if response.status_code == 200:
                models = [m["name"] for m in response.json().get("models", [])]
                if any("sqlcoder" in m for m in models):
                    OLLAMA_AVAILABLE = True
                    logger.info("[LLM] Ollama detectado con sqlcoder")
                    return True
    except Exception as e:
        logger.debug(f"[LLM] Ollama no disponible: {e}")
    return False


# Inicializar al importar
check_ollama()

# Importar clientes segun disponibilidad
if USE_CLAUDE:
    import anthropic
    claude_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    logger.info("[LLM] Claude configurado")

if USE_GEMINI:
    import google.generativeai as genai
    genai.configure(api_key=GEMINI_API_KEY)
    logger.info("[LLM] Gemini configurado")

if not USE_CLAUDE and not USE_GEMINI:
    logger.warning("[LLM] No hay API key configurada para analisis")


# === GENERACION SQL ===

def generar_sql_ollama(pregunta: str) -> dict:
    """Genera SQL usando sqlcoder via Ollama."""
    prompt = f"""### Task
Generate a SQL query to answer the following question: `{pregunta}`

### Database Schema
{DB_SCHEMA}

### SQL
Only respond with the SQL query, no explanation. Use LIMIT {Config.SQL_LIMIT}.
"""
    try:
        with httpx.Client(timeout=60.0) as http_client:
            response = http_client.post(
                f"{Config.OLLAMA_URL}/api/generate",
                json={
                    "model": Config.OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": Config.TEMPERATURE, "num_predict": Config.MAX_TOKENS_SQL}
                }
            )
            if response.status_code == 200:
                text = response.json().get("response", "")
                sql = _validar_sql(text)
                if sql:
                    return {"sql": sql, "modelo": "sqlcoder"}
    except Exception as e:
        logger.error(f"[Ollama] Error: {e}")
    return {"sql": None}


def generar_sql_claude(pregunta: str) -> dict:
    """Genera SQL usando Claude."""
    prompt = f"""Genera SOLO una query SQL para PostgreSQL. Sin explicaciones, sin markdown.

{DB_SCHEMA}

Pregunta: {pregunta}

Responde SOLO con el SELECT (maximo {Config.SQL_LIMIT} filas con LIMIT):"""

    try:
        message = claude_client.messages.create(
            model=Config.CLAUDE_MODEL,
            max_tokens=Config.MAX_TOKENS_SQL,
            messages=[{"role": "user", "content": prompt}]
        )
        text = message.content[0].text
        sql = _validar_sql(text)
        if sql:
            return {"sql": sql, "modelo": "claude-haiku"}
        return {"sql": None}
    except Exception as e:
        logger.error(f"[Claude] Error: {e}")
        return {"sql": None, "error": str(e)}


def generar_sql_gemini(pregunta: str) -> dict:
    """Genera SQL usando Gemini."""
    prompt = f"""Genera SOLO una query SQL para PostgreSQL. Sin explicaciones.

{DB_SCHEMA}

Pregunta: {pregunta}

Responde SOLO con el SELECT (maximo {Config.SQL_LIMIT} filas con LIMIT):"""

    try:
        model = genai.GenerativeModel(Config.GEMINI_MODEL)
        response = model.generate_content(prompt)
        sql = _validar_sql(response.text)
        if sql:
            return {"sql": sql, "modelo": "gemini"}
        return {"sql": None}
    except Exception as e:
        logger.error(f"[Gemini] Error: {e}")
        return {"sql": None, "error": str(e)}


# === ANALISIS DE RESULTADOS ===

def _prompt_analisis(pregunta: str, datos: list, columnas: list) -> str:
    """Genera prompt para analisis de datos."""
    datos_str = json.dumps(datos[:10], indent=2, default=str, ensure_ascii=False)
    return f"""Analiza estos datos y responde en espanol con un JSON valido.

Pregunta: {pregunta}
Columnas: {columnas}
Datos ({len(datos)} filas): {datos_str}

Responde SOLO con un JSON (sin markdown, sin ```):
{{"respuesta": "explicacion 2-3 frases", "grafica": {{"tipo": "bar|line|pie|table", "x": "columna_x", "y": "columna_y", "titulo": "Titulo"}}, "insights": ["insight1", "insight2"]}}"""


def analizar_claude(pregunta: str, datos: list, columnas: list) -> dict:
    """Analiza resultados usando Claude."""
    if not datos:
        return _respuesta_vacia()

    try:
        message = claude_client.messages.create(
            model=Config.CLAUDE_MODEL,
            max_tokens=Config.MAX_TOKENS_ANALYSIS,
            messages=[{"role": "user", "content": _prompt_analisis(pregunta, datos, columnas)}]
        )
        result = _extraer_json(message.content[0].text)
        if result:
            return result
    except Exception as e:
        logger.error(f"[Claude] Error analisis: {e}")

    return _respuesta_fallback(datos, columnas)


def analizar_gemini(pregunta: str, datos: list, columnas: list) -> dict:
    """Analiza resultados usando Gemini."""
    if not datos:
        return _respuesta_vacia()

    try:
        model = genai.GenerativeModel(Config.GEMINI_MODEL)
        response = model.generate_content(_prompt_analisis(pregunta, datos, columnas))
        result = _extraer_json(response.text)
        if result:
            return result
    except Exception as e:
        logger.error(f"[Gemini] Error analisis: {e}")

    return _respuesta_fallback(datos, columnas)


# === API PUBLICA ===

def procesar_con_ia(pregunta: str) -> dict:
    """Genera SQL usando el mejor backend: Ollama > Claude > Gemini."""
    if not OLLAMA_AVAILABLE:
        check_ollama()

    if OLLAMA_AVAILABLE:
        result = generar_sql_ollama(pregunta)
        if result.get("sql"):
            return result

    if USE_CLAUDE:
        result = generar_sql_claude(pregunta)
        if result.get("sql"):
            return result

    if USE_GEMINI:
        return generar_sql_gemini(pregunta)

    return {"sql": None, "error": "No hay backend de IA disponible"}


def analizar_resultados(pregunta: str, datos: list, columnas: list) -> dict:
    """Analiza resultados usando Claude o Gemini."""
    if USE_CLAUDE:
        return analizar_claude(pregunta, datos, columnas)
    elif USE_GEMINI:
        return analizar_gemini(pregunta, datos, columnas)
    else:
        return {
            "respuesta": f"Se encontraron {len(datos)} resultados (sin IA para analisis).",
            "grafica": {"tipo": "table", "x": None, "y": None, "titulo": "Resultados"},
            "insights": []
        }
