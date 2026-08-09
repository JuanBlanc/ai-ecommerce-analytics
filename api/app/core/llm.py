"""
Cliente LLM con soporte para:
- Ollama instalado en el host (SQL gratis, opcional)
- Claude (SDK nativo de Anthropic)
- Cualquier backend compatible con la API de OpenAI

Prioridad SQL: Ollama local > Claude > compatible OpenAI
Prioridad Analisis: Claude > compatible OpenAI
"""

import os
import json
import time
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

    # Backend generico compatible con la API de OpenAI:
    # OpenAI, OpenRouter, LM Studio, vLLM o el endpoint /openai de Gemini.
    # Solo hay que cambiar OPENAI_BASE_URL.
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()
    OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").strip().rstrip("/")

    # Ollama corre en el ordenador del usuario, no en un contenedor propio
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "sqlcoder:7b").strip()
    OLLAMA_URL = os.getenv("OLLAMA_URL", "http://host.docker.internal:11434").strip().rstrip("/")
    OLLAMA_CHECK_INTERVAL = 30  # segundos entre re-busquedas del servicio


# Variables de entorno
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "").strip()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
USE_OLLAMA_ENV = os.getenv("USE_OLLAMA", "false").lower() in ("true", "1", "yes")

# Flags de disponibilidad
USE_CLAUDE = bool(ANTHROPIC_API_KEY)
USE_OPENAI = bool(OPENAI_API_KEY)
OLLAMA_AVAILABLE = False

# Modelos instalados en el Ollama del host (se rellena al detectarlo)
OLLAMA_MODELS: list[str] = []

# Momento de la ultima busqueda de Ollama (monotonic)
_ultima_busqueda_ollama = 0.0


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
    """Busca un Ollama en el host y cachea los modelos que tiene instalados."""
    global OLLAMA_AVAILABLE, OLLAMA_MODELS, _ultima_busqueda_ollama
    _ultima_busqueda_ollama = time.monotonic()
    if not USE_OLLAMA_ENV:
        return False
    try:
        with httpx.Client(timeout=2.0) as http_client:
            response = http_client.get(f"{Config.OLLAMA_URL}/api/tags")
            if response.status_code != 200:
                logger.warning(
                    f"[LLM] Ollama respondio {response.status_code} en {Config.OLLAMA_URL}"
                )
                return False

            OLLAMA_MODELS = sorted(m["name"] for m in response.json().get("models", []))
            OLLAMA_AVAILABLE = bool(OLLAMA_MODELS)

            if not OLLAMA_AVAILABLE:
                logger.warning(
                    f"[LLM] Ollama accesible en {Config.OLLAMA_URL} pero sin modelos "
                    f"instalados. Descarga uno con: ollama pull {Config.OLLAMA_MODEL}"
                )
                return False

            logger.info(
                f"[LLM] Ollama detectado en {Config.OLLAMA_URL} con "
                f"{len(OLLAMA_MODELS)} modelo(s): {', '.join(OLLAMA_MODELS)}"
            )
            return True
    except Exception as e:
        logger.info(
            f"[LLM] No se encontro Ollama en {Config.OLLAMA_URL} ({e}). "
            "Se usara Claude o el backend compatible con OpenAI."
        )
    return False


def modelo_ollama_por_defecto() -> str | None:
    """
    Modelo de Ollama a usar: el configurado si esta instalado (tolerando otro
    tag), y si no el primero disponible.
    """
    if not OLLAMA_MODELS:
        return None

    base_configurado = Config.OLLAMA_MODEL.split(":")[0]
    for modelo in OLLAMA_MODELS:
        if modelo == Config.OLLAMA_MODEL or modelo.split(":")[0] == base_configurado:
            return modelo

    logger.warning(
        f"[LLM] {Config.OLLAMA_MODEL} no esta instalado; se usara {OLLAMA_MODELS[0]}. "
        f"Para generar SQL conviene: ollama pull {Config.OLLAMA_MODEL}"
    )
    return OLLAMA_MODELS[0]


# Inicializar al importar
check_ollama()

# Importar clientes segun disponibilidad
if USE_CLAUDE:
    import anthropic
    claude_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    logger.info("[LLM] Claude configurado")

if USE_OPENAI:
    from openai import OpenAI
    openai_client = OpenAI(api_key=OPENAI_API_KEY, base_url=Config.OPENAI_BASE_URL)
    logger.info(
        f"[LLM] Backend compatible OpenAI configurado en {Config.OPENAI_BASE_URL} "
        f"(modelo {Config.OPENAI_MODEL})"
    )

if not USE_CLAUDE and not USE_OPENAI:
    logger.warning("[LLM] No hay API key configurada para analisis")


# === GENERACION SQL ===

def _prompt_sql(pregunta: str) -> str:
    """Prompt de generacion de SQL para los backends conversacionales."""
    return f"""Genera SOLO una query SQL para PostgreSQL. Sin explicaciones, sin markdown.

{DB_SCHEMA}

Pregunta: {pregunta}

Responde SOLO con el SELECT (maximo {Config.SQL_LIMIT} filas con LIMIT):"""


def generar_sql_ollama(pregunta: str, modelo: str | None = None) -> dict:
    """Genera SQL usando el Ollama instalado en el host."""
    modelo = modelo or modelo_ollama_por_defecto()
    if not modelo:
        return {"sql": None}

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
                    "model": modelo,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": Config.TEMPERATURE, "num_predict": Config.MAX_TOKENS_SQL}
                }
            )
            if response.status_code == 200:
                text = response.json().get("response", "")
                sql = _validar_sql(text)
                if sql:
                    return {"sql": sql, "modelo": modelo}
    except Exception as e:
        logger.error(f"[Ollama] Error: {e}")
    return {"sql": None}


def generar_sql_claude(pregunta: str, modelo: str | None = None) -> dict:
    """Genera SQL usando Claude."""
    modelo = modelo or Config.CLAUDE_MODEL
    try:
        message = claude_client.messages.create(
            model=modelo,
            max_tokens=Config.MAX_TOKENS_SQL,
            messages=[{"role": "user", "content": _prompt_sql(pregunta)}]
        )
        text = message.content[0].text
        sql = _validar_sql(text)
        if sql:
            return {"sql": sql, "modelo": modelo}
        return {"sql": None}
    except Exception as e:
        logger.error(f"[Claude] Error: {e}")
        return {"sql": None, "error": str(e)}


def generar_sql_openai(pregunta: str, modelo: str | None = None) -> dict:
    """Genera SQL con cualquier backend compatible con la API de OpenAI."""
    modelo = modelo or Config.OPENAI_MODEL
    try:
        response = openai_client.chat.completions.create(
            model=modelo,
            max_tokens=Config.MAX_TOKENS_SQL,
            temperature=Config.TEMPERATURE,
            messages=[{"role": "user", "content": _prompt_sql(pregunta)}]
        )
        sql = _validar_sql(response.choices[0].message.content or "")
        if sql:
            return {"sql": sql, "modelo": modelo}
        return {"sql": None}
    except Exception as e:
        logger.error(f"[OpenAI] Error: {e}")
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


def analizar_openai(pregunta: str, datos: list, columnas: list) -> dict:
    """Analiza resultados con el backend compatible con OpenAI."""
    if not datos:
        return _respuesta_vacia()

    try:
        response = openai_client.chat.completions.create(
            model=Config.OPENAI_MODEL,
            max_tokens=Config.MAX_TOKENS_ANALYSIS,
            temperature=Config.TEMPERATURE,
            messages=[{"role": "user", "content": _prompt_analisis(pregunta, datos, columnas)}]
        )
        result = _extraer_json(response.choices[0].message.content or "")
        if result:
            return result
    except Exception as e:
        logger.error(f"[OpenAI] Error analisis: {e}")

    return _respuesta_fallback(datos, columnas)


# === API PUBLICA ===

def ollama_disponible() -> bool:
    """
    Estado actual de Ollama en el host.
    Si aun no se detecto, vuelve a buscarlo como mucho cada OLLAMA_CHECK_INTERVAL
    para no penalizar cada peticion con el timeout de conexion.
    """
    if OLLAMA_AVAILABLE or not USE_OLLAMA_ENV:
        return OLLAMA_AVAILABLE

    if time.monotonic() - _ultima_busqueda_ollama >= Config.OLLAMA_CHECK_INTERVAL:
        check_ollama()

    return OLLAMA_AVAILABLE


def listar_backends() -> list[dict]:
    """
    Backends de IA y modelos seleccionables desde el cliente.
    Solo Ollama expone varios modelos; Claude y el compatible-OpenAI exponen
    el que tienen configurado.
    """
    return [
        {
            "id": "ollama",
            "nombre": "Ollama local",
            "disponible": ollama_disponible(),
            "modelos": list(OLLAMA_MODELS),
            "modelo_por_defecto": modelo_ollama_por_defecto(),
        },
        {
            "id": "claude",
            "nombre": "Claude (Anthropic)",
            "disponible": USE_CLAUDE,
            "modelos": [Config.CLAUDE_MODEL] if USE_CLAUDE else [],
            "modelo_por_defecto": Config.CLAUDE_MODEL if USE_CLAUDE else None,
        },
        {
            "id": "openai",
            "nombre": "Compatible OpenAI",
            "disponible": USE_OPENAI,
            "modelos": [Config.OPENAI_MODEL] if USE_OPENAI else [],
            "modelo_por_defecto": Config.OPENAI_MODEL if USE_OPENAI else None,
        },
    ]


def backend_disponible(backend: str) -> bool:
    """Indica si un backend concreto puede atender peticiones ahora mismo."""
    if backend == "ollama":
        return ollama_disponible()
    if backend == "claude":
        return USE_CLAUDE
    if backend == "openai":
        return USE_OPENAI
    return False


def procesar_con_ia(pregunta: str, backend: str | None = None, modelo: str | None = None) -> dict:
    """
    Genera SQL. Con `backend` se usa solo ese (sin caer a otro, para que la
    eleccion del usuario no se ignore en silencio); sin el, cadena automatica
    Ollama local > Claude > compatible OpenAI.
    """
    if backend:
        generadores = {
            "ollama": generar_sql_ollama,
            "claude": generar_sql_claude,
            "openai": generar_sql_openai,
        }
        generador = generadores.get(backend)
        if not generador:
            return {"sql": None, "error": f"Backend desconocido: {backend}"}
        if not backend_disponible(backend):
            return {"sql": None, "error": f"El backend '{backend}' no esta disponible"}
        return generador(pregunta, modelo)

    if ollama_disponible():
        result = generar_sql_ollama(pregunta)
        if result.get("sql"):
            return result

    if USE_CLAUDE:
        result = generar_sql_claude(pregunta)
        if result.get("sql"):
            return result

    if USE_OPENAI:
        return generar_sql_openai(pregunta)

    return {"sql": None, "error": "No hay backend de IA disponible"}


def analizar_resultados(pregunta: str, datos: list, columnas: list) -> dict:
    """Analiza resultados usando Claude o el backend compatible con OpenAI."""
    if USE_CLAUDE:
        return analizar_claude(pregunta, datos, columnas)
    elif USE_OPENAI:
        return analizar_openai(pregunta, datos, columnas)
    else:
        return {
            "respuesta": f"Se encontraron {len(datos)} resultados (sin IA para analisis).",
            "grafica": {"tipo": "table", "x": None, "y": None, "titulo": "Resultados"},
            "insights": []
        }
