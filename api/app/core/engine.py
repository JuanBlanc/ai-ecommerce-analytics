"""
Motor de procesamiento de preguntas del modulo CORE.
Usa Claude, un backend compatible con OpenAI o un Ollama local para generar
SQL y analizar.

Punto de entrada del modulo: la API importa estas funciones, no las reimplementa.
"""

from .llm import (
    procesar_con_ia,
    analizar_resultados,
    ollama_disponible,
    modelo_ollama_por_defecto,
    listar_backends,
    Config,
    USE_CLAUDE,
    USE_OPENAI
)


def get_backend_info() -> str:
    """Devuelve info de los backends disponibles."""
    backends = []
    if ollama_disponible():
        backends.append(f"Ollama local ({modelo_ollama_por_defecto()})")
    if USE_CLAUDE:
        backends.append("Claude")
    if USE_OPENAI:
        backends.append(f"Compatible OpenAI ({Config.OPENAI_MODEL})")
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
