from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from ..database import get_db
from ..models import Product, ProductCategory, OrderItem, Order
from ..schemas import ProductResponse, CategoryResponse

router = APIRouter(prefix="/products", tags=["Products"])


@router.get("/", response_model=List[ProductResponse])
def listar_products(
    skip: int = 0,
    limit: int = Query(default=50, le=100),
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Listar productos con filtros opcionales"""
    query = db.query(Product)

    if category:
        query = query.filter(Product.product_category_name.ilike(f"%{category}%"))

    return query.offset(skip).limit(limit).all()


@router.get("/count")
def contar_products(db: Session = Depends(get_db)):
    """Contar total de productos"""
    return {"count": db.query(func.count(Product.product_id)).scalar()}


@router.get("/categories", response_model=List[CategoryResponse])
def listar_categorias(db: Session = Depends(get_db)):
    """Listar todas las categorías"""
    return db.query(ProductCategory).order_by(ProductCategory.product_category_name_english).all()


@router.get("/by-category")
def productos_por_categoria(limit: int = 20, db: Session = Depends(get_db)):
    """Obtener productos agrupados por categoría"""
    resultados = db.query(
        Product.product_category_name,
        func.count(Product.product_id).label("count")
    ).group_by(Product.product_category_name
    ).order_by(func.count(Product.product_id).desc()
    ).limit(limit).all()

    return [
        {"category": r.product_category_name, "count": r.count}
        for r in resultados
    ]


@router.get("/top-selling")
def productos_mas_vendidos(limit: int = 10, db: Session = Depends(get_db)):
    """Obtener los productos más vendidos"""
    resultados = db.query(
        Product.product_id,
        Product.product_category_name,
        func.count(OrderItem.order_item_id).label("times_sold"),
        func.sum(OrderItem.price).label("total_revenue")
    ).join(OrderItem, OrderItem.product_id == Product.product_id
    ).join(Order, Order.order_id == OrderItem.order_id
    ).filter(Order.order_status == 'delivered'
    ).group_by(Product.product_id, Product.product_category_name
    ).order_by(func.count(OrderItem.order_item_id).desc()
    ).limit(limit).all()

    return [
        {
            "product_id": r.product_id[:8] + "...",
            "category": r.product_category_name,
            "times_sold": r.times_sold,
            "total_revenue": float(r.total_revenue) if r.total_revenue else 0
        }
        for r in resultados
    ]


@router.get("/category-revenue")
def revenue_por_categoria(limit: int = 15, db: Session = Depends(get_db)):
    """Obtener ingresos por categoría"""
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


@router.get("/heavy")
def productos_pesados(min_weight: int = 10000, limit: int = 20, db: Session = Depends(get_db)):
    """Obtener productos pesados (más de X gramos)"""
    return db.query(Product).filter(
        Product.product_weight_g >= min_weight
    ).order_by(Product.product_weight_g.desc()).limit(limit).all()


@router.get("/{product_id}", response_model=ProductResponse)
def obtener_product(product_id: str, db: Session = Depends(get_db)):
    """Obtener un producto por ID"""
    product = db.query(Product).filter(Product.product_id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return product
