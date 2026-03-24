"""
Motor de procesamiento de preguntas.
Usa Gemini (si hay API key) o Ollama (local) para generar SQL y analizar.
"""

from .llm import procesar_con_ia, analizar_resultados, USE_GEMINI, SQL_MODEL, CHAT_MODEL


def get_backend_info() -> str:
    """Devuelve info del backend en uso."""
    if USE_GEMINI:
        return "Gemini (API)"
    return f"Ollama local (SQL: {SQL_MODEL}, Chat: {CHAT_MODEL})"


def procesar_pregunta(pregunta: str) -> dict:
    """
    Procesa una pregunta y genera SQL.
    """
    resultado = procesar_con_ia(pregunta)

    sql = resultado.get("sql")

    if not sql:
        return {
            "query_sql": None,
            "respuesta": f"""No pude generar una consulta para esa pregunta.

Prueba con preguntas más específicas como:
• "¿Cuáles son las ventas por estado?"
• "Top 10 productos más vendidos"
• "¿Cuántos pedidos hay por mes?"
• "Clientes que más han gastado"
• "Distribución de métodos de pago"
• "Reviews con puntuación baja"

Backend: {get_backend_info()}""",
            "error": False
        }

    return {
        "query_sql": sql,
        "respuesta": "Consultando...",
        "error": False
    }


def analizar_datos(pregunta: str, datos: list, columnas: list) -> dict:
    """
    Analiza los resultados de una consulta.
    """
    return analizar_resultados(pregunta, datos, columnas)
