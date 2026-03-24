from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List
import httpx
import os
from ..database import get_db
from ..models import QueryLog
from ..schemas import ChatQuery, ChatResponse, GraficaConfig

router = APIRouter(prefix="/chat", tags=["Chatbot IA"])

CORE_URL = os.getenv("CORE_URL", "http://core:8000")


@router.post("/", response_model=ChatResponse)
async def procesar_pregunta(query: ChatQuery, db: Session = Depends(get_db)):
    """
    Procesa una pregunta usando Gemini IA:
    1. Genera SQL desde lenguaje natural
    2. Ejecuta la consulta
    3. Analiza resultados y genera respuesta narrativa
    4. Recomienda tipo de gráfica
    """
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            # 1. Enviar pregunta al CORE para generar SQL
            response = await client.post(
                f"{CORE_URL}/procesar",
                json={"pregunta": query.pregunta}
            )

            if response.status_code != 200:
                raise HTTPException(
                    status_code=500,
                    detail="Error al procesar la pregunta en el módulo CORE"
                )

            resultado_core = response.json()

            # Si hay error en la generación de SQL
            if resultado_core.get("error"):
                return ChatResponse(
                    pregunta=query.pregunta,
                    respuesta=resultado_core.get("respuesta", "Error desconocido"),
                    query_sql=None,
                    datos=None,
                    grafica=None,
                    insights=None,
                    exitosa=False
                )

            query_sql = resultado_core.get("query_sql")
            datos = []
            columnas = []
            respuesta_texto = ""
            grafica = None
            insights = []

            # 2. Ejecutar query si el CORE generó una
            if query_sql:
                try:
                    result = db.execute(text(query_sql))
                    columnas = list(result.keys())
                    datos = [dict(zip(columnas, row)) for row in result.fetchall()]

                    # Convertir tipos para JSON
                    for fila in datos:
                        for key, value in fila.items():
                            if hasattr(value, '__float__'):
                                fila[key] = float(value)
                            elif hasattr(value, 'isoformat'):
                                fila[key] = value.isoformat()

                    # 3. Analizar resultados con IA
                    analisis_response = await client.post(
                        f"{CORE_URL}/analizar",
                        json={
                            "pregunta": query.pregunta,
                            "datos": datos,
                            "columnas": columnas
                        }
                    )

                    if analisis_response.status_code == 200:
                        analisis = analisis_response.json()
                        respuesta_texto = analisis.get("respuesta", "Consulta ejecutada correctamente.")
                        grafica_data = analisis.get("grafica", {})
                        grafica = GraficaConfig(
                            tipo=grafica_data.get("tipo", "table"),
                            x=grafica_data.get("x"),
                            y=grafica_data.get("y"),
                            titulo=grafica_data.get("titulo", "Resultados")
                        )
                        insights = analisis.get("insights", [])
                    else:
                        respuesta_texto = f"Se obtuvieron {len(datos)} resultados."
                        grafica = GraficaConfig(tipo="table", titulo="Resultados")

                except Exception as e:
                    db.rollback()  # Limpiar transacción fallida
                    respuesta_texto = f"Error en la consulta. Intenta reformular la pregunta."
                    query_sql = None
                    datos = []
                    grafica = GraficaConfig(tipo="table", titulo="Error")
            else:
                respuesta_texto = resultado_core.get("respuesta", "No se pudo generar una consulta SQL.")

            # 4. Guardar log
            log = QueryLog(
                pregunta_usuario=query.pregunta,
                query_generada=query_sql,
                respuesta=respuesta_texto,
                exitosa=bool(query_sql and datos)
            )
            db.add(log)
            db.commit()

            return ChatResponse(
                pregunta=query.pregunta,
                respuesta=respuesta_texto,
                query_sql=query_sql,
                datos=datos if datos else None,
                grafica=grafica,
                insights=insights if insights else None,
                exitosa=bool(query_sql)
            )

    except httpx.RequestError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Servicio CORE no disponible: {str(e)}"
        )


@router.get("/historial", response_model=List[dict])
def obtener_historial(limit: int = 50, db: Session = Depends(get_db)):
    """Obtener historial de consultas"""
    logs = db.query(QueryLog).order_by(
        QueryLog.created_at.desc()
    ).limit(limit).all()

    return [
        {
            "id": log.id,
            "pregunta": log.pregunta_usuario,
            "query_sql": log.query_generada,
            "respuesta": log.respuesta,
            "exitosa": log.exitosa,
            "fecha": log.created_at.isoformat() if log.created_at else None
        }
        for log in logs
    ]
