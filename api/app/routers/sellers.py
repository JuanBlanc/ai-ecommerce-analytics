from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from ..database import get_db
from ..models import Seller, OrderItem, Order, OrderReview
from ..schemas import SellerResponse

router = APIRouter(prefix="/sellers", tags=["Sellers"])


@router.get("/", response_model=List[SellerResponse])
def listar_sellers(
    skip: int = 0,
    limit: int = Query(default=50, le=100),
    state: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Listar vendedores con filtros opcionales"""
    query = db.query(Seller)

    if state:
        query = query.filter(Seller.seller_state == state)

    return query.offset(skip).limit(limit).all()


@router.get("/count")
def contar_sellers(db: Session = Depends(get_db)):
    """Contar total de vendedores"""
    return {"count": db.query(func.count(Seller.seller_id)).scalar()}


@router.get("/by-state")
def sellers_por_estado(db: Session = Depends(get_db)):
    """Obtener vendedores agrupados por estado"""
    resultados = db.query(
        Seller.seller_state,
        func.count(Seller.seller_id).label("count")
    ).group_by(Seller.seller_state
    ).order_by(func.count(Seller.seller_id).desc()
    ).all()

    return [{"state": r.seller_state, "count": r.count} for r in resultados]


@router.get("/top-performers")
def top_vendedores(limit: int = 10, db: Session = Depends(get_db)):
    """Obtener los vendedores con más ventas"""
    resultados = db.query(
        Seller.seller_id,
        Seller.seller_city,
        Seller.seller_state,
        func.count(func.distinct(OrderItem.order_id)).label("total_orders"),
        func.sum(OrderItem.price).label("total_revenue")
    ).join(OrderItem, OrderItem.seller_id == Seller.seller_id
    ).join(Order, Order.order_id == OrderItem.order_id
    ).filter(Order.order_status == 'delivered'
    ).group_by(Seller.seller_id, Seller.seller_city, Seller.seller_state
    ).order_by(func.sum(OrderItem.price).desc()
    ).limit(limit).all()

    return [
        {
            "seller_id": r.seller_id[:8] + "...",
            "city": r.seller_city,
            "state": r.seller_state,
            "total_orders": r.total_orders,
            "total_revenue": float(r.total_revenue) if r.total_revenue else 0
        }
        for r in resultados
    ]


@router.get("/best-rated")
def vendedores_mejor_valorados(limit: int = 10, db: Session = Depends(get_db)):
    """Obtener vendedores mejor valorados"""
    resultados = db.query(
        Seller.seller_id,
        Seller.seller_city,
        Seller.seller_state,
        func.avg(OrderReview.review_score).label("avg_score"),
        func.count(OrderReview.review_id).label("total_reviews")
    ).join(OrderItem, OrderItem.seller_id == Seller.seller_id
    ).join(Order, Order.order_id == OrderItem.order_id
    ).join(OrderReview, OrderReview.order_id == Order.order_id
    ).group_by(Seller.seller_id, Seller.seller_city, Seller.seller_state
    ).having(func.count(OrderReview.review_id) >= 10
    ).order_by(func.avg(OrderReview.review_score).desc()
    ).limit(limit).all()

    return [
        {
            "seller_id": r.seller_id[:8] + "...",
            "city": r.seller_city,
            "state": r.seller_state,
            "avg_score": round(float(r.avg_score), 2) if r.avg_score else 0,
            "total_reviews": r.total_reviews
        }
        for r in resultados
    ]


@router.get("/{seller_id}", response_model=SellerResponse)
def obtener_seller(seller_id: str, db: Session = Depends(get_db)):
    """Obtener un vendedor por ID"""
    seller = db.query(Seller).filter(Seller.seller_id == seller_id).first()
    if not seller:
        raise HTTPException(status_code=404, detail="Vendedor no encontrado")
    return seller


@router.get("/{seller_id}/stats")
def stats_seller(seller_id: str, db: Session = Depends(get_db)):
    """Obtener estadísticas de un vendedor"""
    seller = db.query(Seller).filter(Seller.seller_id == seller_id).first()
    if not seller:
        raise HTTPException(status_code=404, detail="Vendedor no encontrado")

    stats = db.query(
        func.count(func.distinct(OrderItem.order_id)).label("total_orders"),
        func.sum(OrderItem.price).label("total_revenue"),
        func.avg(OrderItem.price).label("avg_price")
    ).filter(OrderItem.seller_id == seller_id).first()

    return {
        "seller_id": seller_id,
        "city": seller.seller_city,
        "state": seller.seller_state,
        "total_orders": stats.total_orders or 0,
        "total_revenue": float(stats.total_revenue) if stats.total_revenue else 0,
        "avg_price": float(stats.avg_price) if stats.avg_price else 0
    }
