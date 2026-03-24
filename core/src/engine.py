"""
Motor de procesamiento de preguntas.
Usa Claude, Gemini o Ollama para generar SQL y analizar.
"""

from .llm import (
    procesar_con_ia,
    analizar_resultados,
    USE_CLAUDE,
    USE_GEMINI,
    OLLAMA_AVAILABLE
)


def get_backend_info() -> str:
    """Devuelve info de los backends disponibles."""
    backends = []
    if OLLAMA_AVAILABLE:
        backends.append("Ollama (sqlcoder)")
    if USE_CLAUDE:
        backends.append("Claude")
    if USE_GEMINI:
        backends.append("Gemini")
    return " > ".join(backends) if backends else "Sin backend configurado"


def procesar_pregunta(pregunta: str) -> dict:
    """Procesa una pregunta y genera SQL."""
    resultado = procesar_con_ia(pregunta)
    sql = resultado.get("sql")
    modelo = resultado.get("modelo", "desconocido")

    if not sql:
        return {
            "query_sql": None,
            "respuesta": f"""No pude generar una consulta para esa pregunta.

Prueba con preguntas mas especificas como:
- Cuales son las ventas por estado?
- Top 10 productos mas vendidos
- Cuantos pedidos hay por mes?
- Clientes que mas han gastado
- Distribucion de metodos de pago

Backend: {get_backend_info()}""",
            "error": False
        }

    return {
        "query_sql": sql,
        "respuesta": f"Consultando con {modelo}...",
        "error": False
    }


def analizar_datos(pregunta: str, datos: list, columnas: list) -> dict:
    """Analiza los resultados de una consulta."""
    return analizar_resultados(pregunta, datos, columnas)
