from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from typing import List, Optional
from ..database import get_db
from ..models import Order, OrderItem, Customer, OrderPayment, OrderReview
from ..schemas import OrderResponse, OrderSummary

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.get("/", response_model=List[OrderResponse])
def listar_orders(
    skip: int = 0,
    limit: int = Query(default=50, le=100),
    status: Optional[str] = None,
    customer_state: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Listar pedidos con filtros opcionales"""
    query = db.query(Order).join(Customer)

    if status:
        query = query.filter(Order.order_status == status)
    if customer_state:
        query = query.filter(Customer.customer_state == customer_state)

    return query.order_by(Order.order_purchase_timestamp.desc()).offset(skip).limit(limit).all()


@router.get("/count")
def contar_orders(
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Contar pedidos por estado"""
    query = db.query(func.count(Order.order_id))
    if status:
        query = query.filter(Order.order_status == status)
    return {"count": query.scalar()}


@router.get("/by-status")
def orders_por_estado(db: Session = Depends(get_db)):
    """Obtener cantidad de pedidos por estado"""
    resultados = db.query(
        Order.order_status,
        func.count(Order.order_id).label("count")
    ).group_by(Order.order_status).all()

    return [{"status": r.order_status, "count": r.count} for r in resultados]


@router.get("/by-state")
def orders_por_estado_cliente(limit: int = 10, db: Session = Depends(get_db)):
    """Obtener pedidos agrupados por estado del cliente"""
    resultados = db.query(
        Customer.customer_state,
        func.count(Order.order_id).label("total_orders"),
        func.sum(OrderItem.price).label("total_revenue")
    ).join(Order, Order.customer_id == Customer.customer_id
    ).join(OrderItem, OrderItem.order_id == Order.order_id
    ).group_by(Customer.customer_state
    ).order_by(func.count(Order.order_id).desc()
    ).limit(limit).all()

    return [
        {
            "state": r.customer_state,
            "total_orders": r.total_orders,
            "total_revenue": float(r.total_revenue) if r.total_revenue else 0
        }
        for r in resultados
    ]


@router.get("/monthly")
def orders_mensuales(year: int = 2018, db: Session = Depends(get_db)):
    """Obtener pedidos agrupados por mes"""
    query = text("""
        SELECT
            EXTRACT(MONTH FROM order_purchase_timestamp) as month,
            COUNT(*) as total_orders,
            SUM(oi.price) as total_revenue
        FROM orders o
        JOIN order_items oi ON oi.order_id = o.order_id
        WHERE EXTRACT(YEAR FROM order_purchase_timestamp) = :year
        GROUP BY EXTRACT(MONTH FROM order_purchase_timestamp)
        ORDER BY month
    """)

    result = db.execute(query, {"year": year})
    return [
        {
            "month": int(r.month),
            "total_orders": r.total_orders,
            "total_revenue": float(r.total_revenue) if r.total_revenue else 0
        }
        for r in result
    ]


@router.get("/{order_id}", response_model=OrderResponse)
def obtener_order(order_id: str, db: Session = Depends(get_db)):
    """Obtener un pedido por ID"""
    order = db.query(Order).filter(Order.order_id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    return order


@router.get("/{order_id}/reviews")
def obtener_reviews_order(order_id: str, db: Session = Depends(get_db)):
    """Obtener reviews de un pedido"""
    reviews = db.query(OrderReview).filter(OrderReview.order_id == order_id).all()
    return [
        {
            "review_id": r.review_id,
            "score": r.review_score,
            "title": r.review_comment_title,
            "message": r.review_comment_message,
            "date": r.review_creation_date
        }
        for r in reviews
    ]
