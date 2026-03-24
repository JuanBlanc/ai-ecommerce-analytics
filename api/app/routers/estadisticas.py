from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from decimal import Decimal
from ..database import get_db
from ..models import Order, Customer, Product, Seller, OrderItem, OrderReview, OrderPayment

router = APIRouter(prefix="/estadisticas", tags=["Estadísticas"])


@router.get("/")
def obtener_estadisticas(db: Session = Depends(get_db)):
    """Obtener estadísticas generales del sistema"""
    total_orders = db.query(func.count(Order.order_id)).scalar() or 0
    total_customers = db.query(func.count(Customer.customer_id)).scalar() or 0
    total_products = db.query(func.count(Product.product_id)).scalar() or 0
    total_sellers = db.query(func.count(Seller.seller_id)).scalar() or 0

    revenue = db.query(func.sum(OrderItem.price)).join(
        Order, Order.order_id == OrderItem.order_id
    ).filter(Order.order_status == 'delivered').scalar() or 0

    avg_order = db.query(func.avg(OrderItem.price)).scalar() or 0

    delivered = db.query(func.count(Order.order_id)).filter(
        Order.order_status == 'delivered'
    ).scalar() or 0

    canceled = db.query(func.count(Order.order_id)).filter(
        Order.order_status == 'canceled'
    ).scalar() or 0

    avg_review = db.query(func.avg(OrderReview.review_score)).scalar() or 0

    return {
        "total_orders": total_orders,
        "total_customers": total_customers,
        "total_products": total_products,
        "total_sellers": total_sellers,
        "total_revenue": float(revenue),
        "avg_order_value": round(float(avg_order), 2),
        "orders_delivered": delivered,
        "orders_canceled": canceled,
        "avg_review_score": round(float(avg_review), 2)
    }


@router.get("/revenue-by-state")
def revenue_por_estado(limit: int = 10, db: Session = Depends(get_db)):
    """Ingresos por estado del cliente"""
    resultados = db.query(
        Customer.customer_state,
        func.count(func.distinct(Order.order_id)).label("total_orders"),
        func.sum(OrderItem.price).label("total_revenue"),
        func.avg(OrderItem.price).label("avg_order_value")
    ).join(Order, Order.customer_id == Customer.customer_id
    ).join(OrderItem, OrderItem.order_id == Order.order_id
    ).filter(Order.order_status == 'delivered'
    ).group_by(Customer.customer_state
    ).order_by(func.sum(OrderItem.price).desc()
    ).limit(limit).all()

    return [
        {
            "state": r.customer_state,
            "total_orders": r.total_orders,
            "total_revenue": float(r.total_revenue) if r.total_revenue else 0,
            "avg_order_value": round(float(r.avg_order_value), 2) if r.avg_order_value else 0
        }
        for r in resultados
    ]


@router.get("/revenue-by-category")
def revenue_por_categoria(limit: int = 15, db: Session = Depends(get_db)):
    """Ingresos por categoría de producto"""
    resultados = db.query(
        Product.product_category_name,
        func.count(OrderItem.order_item_id).label("items_sold"),
        func.sum(OrderItem.price).label("total_revenue")
    ).join(OrderItem, OrderItem.product_id == Product.product_id
    ).join(Order, Order.order_id == OrderItem.order_id
    ).filter(Order.order_status == 'delivered'
    ).group_by(Product.product_category_name
    ).order_by(func.sum(OrderItem.price).desc()
    ).limit(limit).all()

    return [
        {
            "category": r.product_category_name,
            "items_sold": r.items_sold,
            "total_revenue": float(r.total_revenue) if r.total_revenue else 0
        }
        for r in resultados
    ]


@router.get("/payment-methods")
def metodos_pago(db: Session = Depends(get_db)):
    """Distribución de métodos de pago"""
    resultados = db.query(
        OrderPayment.payment_type,
        func.count(OrderPayment.order_id).label("count"),
        func.sum(OrderPayment.payment_value).label("total_value")
    ).group_by(OrderPayment.payment_type
    ).order_by(func.count(OrderPayment.order_id).desc()
    ).all()

    return [
        {
            "payment_type": r.payment_type,
            "count": r.count,
            "total_value": float(r.total_value) if r.total_value else 0
        }
        for r in resultados
    ]


@router.get("/delivery-performance")
def rendimiento_entregas(db: Session = Depends(get_db)):
    """Análisis de rendimiento de entregas"""
    query = text("""
        SELECT
            CASE
                WHEN order_delivered_customer_date <= order_estimated_delivery_date THEN 'on_time'
                WHEN order_delivered_customer_date > order_estimated_delivery_date THEN 'late'
                ELSE 'pending'
            END as delivery_status,
            COUNT(*) as count
        FROM orders
        WHERE order_status = 'delivered'
        GROUP BY delivery_status
    """)

    result = db.execute(query)
    return [{"status": r.delivery_status, "count": r.count} for r in result]


@router.get("/monthly-trends")
def tendencias_mensuales(db: Session = Depends(get_db)):
    """Tendencias mensuales de ventas"""
    query = text("""
        SELECT
            TO_CHAR(o.order_purchase_timestamp, 'YYYY-MM') as month,
            COUNT(DISTINCT o.order_id) as total_orders,
            SUM(oi.price) as total_revenue,
            COUNT(DISTINCT o.customer_id) as unique_customers
        FROM orders o
        JOIN order_items oi ON oi.order_id = o.order_id
        WHERE o.order_status = 'delivered'
        GROUP BY TO_CHAR(o.order_purchase_timestamp, 'YYYY-MM')
        ORDER BY month
    """)

    result = db.execute(query)
    return [
        {
            "month": r.month,
            "total_orders": r.total_orders,
            "total_revenue": float(r.total_revenue) if r.total_revenue else 0,
            "unique_customers": r.unique_customers
        }
        for r in result
    ]


@router.get("/freight-analysis")
def analisis_flete(db: Session = Depends(get_db)):
    """Análisis de costos de flete por estado"""
    resultados = db.query(
        Customer.customer_state,
        func.avg(OrderItem.freight_value).label("avg_freight"),
        func.sum(OrderItem.freight_value).label("total_freight"),
        func.count(OrderItem.order_item_id).label("total_items")
    ).join(Order, Order.customer_id == Customer.customer_id
    ).join(OrderItem, OrderItem.order_id == Order.order_id
    ).group_by(Customer.customer_state
    ).order_by(func.avg(OrderItem.freight_value).desc()
    ).limit(10).all()

    return [
        {
            "state": r.customer_state,
            "avg_freight": round(float(r.avg_freight), 2) if r.avg_freight else 0,
            "total_freight": float(r.total_freight) if r.total_freight else 0,
            "total_items": r.total_items
        }
        for r in resultados
    ]
