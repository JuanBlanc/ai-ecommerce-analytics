"""
API del módulo CORE - Procesamiento con IA
Soporta: Gemini (API) u Ollama (local)
"""

from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional, List
from .engine import procesar_pregunta, analizar_datos, get_backend_info

app = FastAPI(
    title="CORE - Motor IA",
    description="Genera SQL y analiza resultados usando Gemini u Ollama",
    version="3.0.0"
)


class PreguntaInput(BaseModel):
    pregunta: str


class AnalisisInput(BaseModel):
    pregunta: str
    datos: List[dict]
    columnas: List[str]


class GraficaConfig(BaseModel):
    tipo: str
    x: Optional[str] = None
    y: Optional[str] = None
    titulo: str


class PreguntaOutput(BaseModel):
    query_sql: Optional[str] = None
    respuesta: str
    error: bool = False


class AnalisisOutput(BaseModel):
    respuesta: str
    grafica: GraficaConfig
    insights: List[str]


@app.get("/")
def root():
    """Endpoint raíz"""
    return {
        "servicio": "CORE - Motor IA",
        "version": "3.0.0",
        "backend": get_backend_info(),
        "descripcion": "Genera SQL y analiza resultados"
    }


@app.get("/health")
def health_check():
    """Health check"""
    return {
        "status": "healthy",
        "backend": get_backend_info()
    }


@app.post("/procesar", response_model=PreguntaOutput)
def procesar(input_data: PreguntaInput):
    """
    Procesa una pregunta y genera SQL.
    """
    resultado = procesar_pregunta(input_data.pregunta)
    return PreguntaOutput(**resultado)


@app.post("/analizar", response_model=AnalisisOutput)
def analizar(input_data: AnalisisInput):
    """
    Analiza los resultados de una consulta.
    """
    resultado = analizar_datos(
        input_data.pregunta,
        input_data.datos,
        input_data.columnas
    )
    return AnalisisOutput(
        respuesta=resultado.get("respuesta", ""),
        grafica=GraficaConfig(**resultado.get("grafica", {"tipo": "table", "titulo": "Resultados"})),
        insights=resultado.get("insights", [])
    )
