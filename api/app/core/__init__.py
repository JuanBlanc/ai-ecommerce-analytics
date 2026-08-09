"""
Modulo CORE - Logica de IA del sistema.

Vive como paquete independiente dentro de la API y se consume importandolo,
nunca escribiendo la logica dentro de los routers. No accede a la base de
datos: recibe la pregunta, devuelve SQL, y analiza los datos que la API le pasa.

API publica del modulo:
    procesar_pregunta(pregunta) -> dict con query_sql / respuesta
    analizar_datos(pregunta, datos, columnas) -> dict con respuesta / grafica / insights
    get_backend_info() -> str con los backends de IA disponibles
"""

from .engine import procesar_pregunta, analizar_datos, get_backend_info

__all__ = ["procesar_pregunta", "analizar_datos", "get_backend_info"]
