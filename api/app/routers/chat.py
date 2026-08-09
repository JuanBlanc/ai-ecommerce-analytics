from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List
from ..database import get_db
from ..models import QueryLog
from ..schemas import ChatQuery, ChatResponse, GraficaConfig, BackendIA
from ..core import procesar_pregunta, analizar_datos, listar_backends

router = APIRouter(prefix="/chat", tags=["Chatbot IA"])


def _convertir_tipos(datos: List[dict]) -> None:
    """Convierte los tipos de la BD (Decimal, datetime) a valores serializables."""
    for fila in datos:
        for key, value in fila.items():
            if hasattr(value, '__float__'):
                fila[key] = float(value)
            elif hasattr(value, 'isoformat'):
                fila[key] = value.isoformat()


def _validar_seleccion(query: ChatQuery) -> None:
    """
    Valida que el backend elegido este disponible y que el modelo pertenezca a
    el. El tipo Literal de ChatQuery ya descarta ids desconocidos (422).
    """
    if not query.backend:
        return

    elegido = next(b for b in listar_backends() if b["id"] == query.backend)

    if not elegido["disponible"]:
        raise HTTPException(
            status_code=400,
            detail=f"El backend '{query.backend}' no esta disponible. "
                   "Consulta GET /chat/modelos."
        )

    if query.modelo and query.modelo not in elegido["modelos"]:
        raise HTTPException(
            status_code=400,
            detail=f"El modelo '{query.modelo}' no esta disponible en "
                   f"'{query.backend}'. Opciones: {', '.join(elegido['modelos'])}"
        )


@router.post("/", response_model=ChatResponse)
def procesar_consulta(query: ChatQuery, db: Session = Depends(get_db)):
    """
    Procesa una pregunta en lenguaje natural con el modulo CORE:
    1. Genera SQL desde lenguaje natural
    2. Ejecuta la consulta
    3. Analiza resultados y genera respuesta narrativa
    4. Recomienda tipo de grafica

    Acepta `backend` y `modelo` opcionales para elegir con que generar el SQL;
    sin ellos se usa la cadena automatica del CORE.

    Endpoint sincrono a proposito: el CORE hace llamadas de red bloqueantes al
    LLM, asi que FastAPI lo ejecuta en su threadpool y no bloquea el event loop.
    """
    _validar_seleccion(query)

    # 1. El CORE genera el SQL a partir de la pregunta
    try:
        resultado_core = procesar_pregunta(query.pregunta, query.backend, query.modelo)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al procesar la pregunta en el modulo CORE: {e}"
        )

    modelo_usado = resultado_core.get("modelo")

    # Si hay error en la generacion de SQL
    if resultado_core.get("error"):
        return ChatResponse(
            pregunta=query.pregunta,
            respuesta=resultado_core.get("respuesta", "Error desconocido"),
            query_sql=None,
            datos=None,
            grafica=None,
            insights=None,
            modelo_usado=modelo_usado,
            exitosa=False
        )

    query_sql = resultado_core.get("query_sql")
    datos = []
    columnas = []
    respuesta_texto = ""
    grafica = None
    insights = []

    # 2. Ejecutar query si el CORE genero una
    if query_sql:
        try:
            result = db.execute(text(query_sql))
            columnas = list(result.keys())
            datos = [dict(zip(columnas, row)) for row in result.fetchall()]
            _convertir_tipos(datos)
        except Exception:
            db.rollback()  # Limpiar transaccion fallida
            respuesta_texto = "Error en la consulta. Intenta reformular la pregunta."
            query_sql = None
            datos = []
            grafica = GraficaConfig(tipo="table", titulo="Error")
        else:
            # 3. Analizar resultados con IA
            try:
                analisis = analizar_datos(query.pregunta, datos, columnas)
                respuesta_texto = analisis.get("respuesta", "Consulta ejecutada correctamente.")
                grafica_data = analisis.get("grafica", {})
                grafica = GraficaConfig(
                    tipo=grafica_data.get("tipo", "table"),
                    x=grafica_data.get("x"),
                    y=grafica_data.get("y"),
                    titulo=grafica_data.get("titulo", "Resultados")
                )
                insights = analisis.get("insights", [])
            except Exception:
                respuesta_texto = f"Se obtuvieron {len(datos)} resultados."
                grafica = GraficaConfig(tipo="table", titulo="Resultados")
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
        modelo_usado=modelo_usado,
        exitosa=bool(query_sql)
    )


@router.get("/modelos", response_model=List[BackendIA])
def listar_modelos():
    """
    Backends de IA disponibles y modelos seleccionables.
    Ollama devuelve todos los modelos que tenga instalados en el host.
    """
    return listar_backends()


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
