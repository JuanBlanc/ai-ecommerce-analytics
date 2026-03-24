from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from ..database import get_db
from ..models import Customer, Order, OrderItem
from ..schemas import CustomerResponse

router = APIRouter(prefix="/customers", tags=["Customers"])


@router.get("/", response_model=List[CustomerResponse])
def listar_customers(
    skip: int = 0,
    limit: int = Query(default=50, le=100),
    state: Optional[str] = None,
    city: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Listar clientes con filtros opcionales"""
    query = db.query(Customer)

    if state:
        query = query.filter(Customer.customer_state == state)
    if city:
        query = query.filter(Customer.customer_city.ilike(f"%{city}%"))

    return query.offset(skip).limit(limit).all()


@router.get("/count")
def contar_customers(db: Session = Depends(get_db)):
    """Contar total de clientes"""
    total = db.query(func.count(Customer.customer_id)).scalar()
    unique = db.query(func.count(func.distinct(Customer.customer_unique_id))).scalar()
    return {"total": total, "unique": unique}


@router.get("/by-state")
def customers_por_estado(limit: int = 27, db: Session = Depends(get_db)):
    """Obtener clientes agrupados por estado"""
    resultados = db.query(
        Customer.customer_state,
        func.count(Customer.customer_id).label("count")
    ).group_by(Customer.customer_state
    ).order_by(func.count(Customer.customer_id).desc()
    ).limit(limit).all()

    return [{"state": r.customer_state, "count": r.count} for r in resultados]


@router.get("/top-spenders")
def top_compradores(limit: int = 10, db: Session = Depends(get_db)):
    """Obtener los clientes que más han gastado"""
    resultados = db.query(
        Customer.customer_id,
        Customer.customer_city,
        Customer.customer_state,
        func.count(Order.order_id).label("total_orders"),
        func.sum(OrderItem.price).label("total_spent")
    ).join(Order, Order.customer_id == Customer.customer_id
    ).join(OrderItem, OrderItem.order_id == Order.order_id
    ).filter(Order.order_status == 'delivered'
    ).group_by(Customer.customer_id, Customer.customer_city, Customer.customer_state
    ).order_by(func.sum(OrderItem.price).desc()
    ).limit(limit).all()

    return [
        {
            "customer_id": r.customer_id[:8] + "...",
            "city": r.customer_city,
            "state": r.customer_state,
            "total_orders": r.total_orders,
            "total_spent": float(r.total_spent) if r.total_spent else 0
        }
        for r in resultados
    ]


@router.get("/cities")
def ciudades_principales(limit: int = 20, db: Session = Depends(get_db)):
    """Obtener las ciudades con más clientes"""
    resultados = db.query(
        Customer.customer_city,
        Customer.customer_state,
        func.count(Customer.customer_id).label("count")
    ).group_by(Customer.customer_city, Customer.customer_state
    ).order_by(func.count(Customer.customer_id).desc()
    ).limit(limit).all()

    return [
        {"city": r.customer_city, "state": r.customer_state, "count": r.count}
        for r in resultados
    ]


@router.get("/{customer_id}", response_model=CustomerResponse)
def obtener_customer(customer_id: str, db: Session = Depends(get_db)):
    """Obtener un cliente por ID"""
    customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return customer


@router.get("/{customer_id}/orders")
def obtener_orders_customer(customer_id: str, db: Session = Depends(get_db)):
    """Obtener pedidos de un cliente"""
    orders = db.query(Order).filter(Order.customer_id == customer_id).all()
    return [
        {
            "order_id": o.order_id,
            "status": o.order_status,
            "purchase_date": o.order_purchase_timestamp
        }
        for o in orders
    ]
