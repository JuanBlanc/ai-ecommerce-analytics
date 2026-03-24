from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from ..database import get_db
from ..models import OrderReview, Order, Product, OrderItem

router = APIRouter(prefix="/reviews", tags=["Reviews"])


@router.get("/")
def listar_reviews(
    skip: int = 0,
    limit: int = Query(default=50, le=100),
    min_score: Optional[int] = None,
    max_score: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Listar reviews con filtros opcionales"""
    query = db.query(OrderReview)

    if min_score:
        query = query.filter(OrderReview.review_score >= min_score)
    if max_score:
        query = query.filter(OrderReview.review_score <= max_score)

    reviews = query.order_by(OrderReview.review_creation_date.desc()).offset(skip).limit(limit).all()

    return [
        {
            "review_id": r.review_id,
            "order_id": r.order_id,
            "score": r.review_score,
            "title": r.review_comment_title,
            "message": r.review_comment_message,
            "date": r.review_creation_date
        }
        for r in reviews
    ]


@router.get("/count")
def contar_reviews(db: Session = Depends(get_db)):
    """Contar total de reviews"""
    return {"count": db.query(func.count(OrderReview.review_id)).scalar()}


@router.get("/distribution")
def distribucion_reviews(db: Session = Depends(get_db)):
    """Obtener distribución de reviews por puntuación"""
    resultados = db.query(
        OrderReview.review_score,
        func.count(OrderReview.review_id).label("count")
    ).group_by(OrderReview.review_score
    ).order_by(OrderReview.review_score
    ).all()

    return [{"score": r.review_score, "count": r.count} for r in resultados]


@router.get("/stats")
def stats_reviews(db: Session = Depends(get_db)):
    """Obtener estadísticas generales de reviews"""
    stats = db.query(
        func.count(OrderReview.review_id).label("total"),
        func.avg(OrderReview.review_score).label("avg_score"),
        func.min(OrderReview.review_score).label("min_score"),
        func.max(OrderReview.review_score).label("max_score")
    ).first()

    # Reviews con comentario
    with_comment = db.query(func.count(OrderReview.review_id)).filter(
        OrderReview.review_comment_message.isnot(None),
        OrderReview.review_comment_message != ""
    ).scalar()

    return {
        "total_reviews": stats.total,
        "avg_score": round(float(stats.avg_score), 2) if stats.avg_score else 0,
        "min_score": stats.min_score,
        "max_score": stats.max_score,
        "with_comments": with_comment
    }


@router.get("/negative")
def reviews_negativas(limit: int = 20, db: Session = Depends(get_db)):
    """Obtener reviews negativas (score 1-2) con comentarios"""
    reviews = db.query(OrderReview).filter(
        OrderReview.review_score <= 2,
        OrderReview.review_comment_message.isnot(None),
        OrderReview.review_comment_message != ""
    ).order_by(OrderReview.review_creation_date.desc()).limit(limit).all()

    return [
        {
            "review_id": r.review_id,
            "order_id": r.order_id,
            "score": r.review_score,
            "message": r.review_comment_message,
            "date": r.review_creation_date
        }
        for r in reviews
    ]


@router.get("/positive")
def reviews_positivas(limit: int = 20, db: Session = Depends(get_db)):
    """Obtener reviews positivas (score 5) con comentarios"""
    reviews = db.query(OrderReview).filter(
        OrderReview.review_score == 5,
        OrderReview.review_comment_message.isnot(None),
        OrderReview.review_comment_message != ""
    ).order_by(OrderReview.review_creation_date.desc()).limit(limit).all()

    return [
        {
            "review_id": r.review_id,
            "order_id": r.order_id,
            "score": r.review_score,
            "message": r.review_comment_message,
            "date": r.review_creation_date
        }
        for r in reviews
    ]


@router.get("/by-category")
def reviews_por_categoria(limit: int = 15, db: Session = Depends(get_db)):
    """Obtener puntuación media por categoría de producto"""
    resultados = db.query(
        Product.product_category_name,
        func.avg(OrderReview.review_score).label("avg_score"),
        func.count(OrderReview.review_id).label("total_reviews")
    ).join(OrderItem, OrderItem.product_id == Product.product_id
    ).join(Order, Order.order_id == OrderItem.order_id
    ).join(OrderReview, OrderReview.order_id == Order.order_id
    ).group_by(Product.product_category_name
    ).having(func.count(OrderReview.review_id) >= 100
    ).order_by(func.avg(OrderReview.review_score).desc()
    ).limit(limit).all()

    return [
        {
            "category": r.product_category_name,
            "avg_score": round(float(r.avg_score), 2),
            "total_reviews": r.total_reviews
        }
        for r in resultados
    ]
