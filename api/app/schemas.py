from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from decimal import Decimal


# ============ CUSTOMERS ============
class CustomerBase(BaseModel):
    customer_id: str
    customer_unique_id: Optional[str] = None
    customer_city: Optional[str] = None
    customer_state: Optional[str] = None


class CustomerResponse(CustomerBase):
    class Config:
        from_attributes = True


# ============ SELLERS ============
class SellerBase(BaseModel):
    seller_id: str
    seller_city: Optional[str] = None
    seller_state: Optional[str] = None


class SellerResponse(SellerBase):
    class Config:
        from_attributes = True


# ============ PRODUCTS ============
class ProductBase(BaseModel):
    product_id: str
    product_category_name: Optional[str] = None
    product_weight_g: Optional[int] = None
    product_length_cm: Optional[int] = None
    product_height_cm: Optional[int] = None
    product_width_cm: Optional[int] = None


class ProductResponse(ProductBase):
    product_photos_qty: Optional[int] = None

    class Config:
        from_attributes = True


# ============ ORDERS ============
class OrderItemResponse(BaseModel):
    order_item_id: int
    product_id: str
    seller_id: str
    price: Decimal
    freight_value: Decimal

    class Config:
        from_attributes = True


class OrderPaymentResponse(BaseModel):
    payment_sequential: int
    payment_type: str
    payment_installments: int
    payment_value: Decimal

    class Config:
        from_attributes = True


class OrderReviewResponse(BaseModel):
    review_id: str
    review_score: int
    review_comment_title: Optional[str] = None
    review_comment_message: Optional[str] = None
    review_creation_date: Optional[datetime] = None

    class Config:
        from_attributes = True


class OrderBase(BaseModel):
    order_id: str
    customer_id: str
    order_status: str
    order_purchase_timestamp: Optional[datetime] = None


class OrderResponse(OrderBase):
    order_approved_at: Optional[datetime] = None
    order_delivered_carrier_date: Optional[datetime] = None
    order_delivered_customer_date: Optional[datetime] = None
    order_estimated_delivery_date: Optional[datetime] = None
    customer: Optional[CustomerResponse] = None
    items: List[OrderItemResponse] = []
    payments: List[OrderPaymentResponse] = []

    class Config:
        from_attributes = True


class OrderSummary(BaseModel):
    order_id: str
    customer_id: str
    customer_city: Optional[str] = None
    customer_state: Optional[str] = None
    order_status: str
    order_purchase_timestamp: Optional[datetime] = None
    total_items: int
    total_price: Decimal
    total_freight: Decimal
    total_order: Decimal


# ============ CATEGORIES ============
class CategoryResponse(BaseModel):
    product_category_name: str
    product_category_name_english: Optional[str] = None

    class Config:
        from_attributes = True


# ============ CHATBOT ============
class ChatQuery(BaseModel):
    pregunta: str


class GraficaConfig(BaseModel):
    tipo: str  # bar, line, pie, table, number
    x: Optional[str] = None
    y: Optional[str] = None
    titulo: str


class ChatResponse(BaseModel):
    pregunta: str
    respuesta: str
    query_sql: Optional[str] = None
    datos: Optional[List[dict]] = None
    grafica: Optional[GraficaConfig] = None
    insights: Optional[List[str]] = None
    exitosa: bool = True


class BackendIA(BaseModel):
    """Backend de IA y los modelos que expone para seleccion en el cliente."""
    id: str
    nombre: str
    disponible: bool
    modelos: List[str] = []
    modelo_por_defecto: Optional[str] = None


# ============ ESTADISTICAS ============
class EstadisticasResponse(BaseModel):
    total_orders: int
    total_customers: int
    total_products: int
    total_sellers: int
    total_revenue: Decimal
    avg_order_value: Decimal
    orders_delivered: int
    orders_canceled: int
    avg_review_score: float


class VentasEstadoResponse(BaseModel):
    customer_state: str
    total_orders: int
    total_revenue: Decimal
    avg_order_value: Decimal


class CategoriaVentasResponse(BaseModel):
    category: str
    total_items: int
    total_revenue: Decimal


class SellerPerformanceResponse(BaseModel):
    seller_id: str
    seller_city: Optional[str]
    seller_state: Optional[str]
    total_orders: int
    total_revenue: Decimal
    avg_review_score: Optional[float]
