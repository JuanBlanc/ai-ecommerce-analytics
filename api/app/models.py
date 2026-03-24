from sqlalchemy import Column, Integer, String, Text, Numeric, Boolean, ForeignKey, TIMESTAMP
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .database import Base


class Geolocation(Base):
    __tablename__ = "geolocation"

    geolocation_zip_code_prefix = Column(String(10), primary_key=True)
    geolocation_lat = Column(Numeric(10, 8))
    geolocation_lng = Column(Numeric(11, 8))
    geolocation_city = Column(String(100))
    geolocation_state = Column(String(2))


class Customer(Base):
    __tablename__ = "customers"

    customer_id = Column(String(50), primary_key=True)
    customer_unique_id = Column(String(50))
    customer_zip_code_prefix = Column(String(10))
    customer_city = Column(String(100))
    customer_state = Column(String(2))

    orders = relationship("Order", back_populates="customer")


class Seller(Base):
    __tablename__ = "sellers"

    seller_id = Column(String(50), primary_key=True)
    seller_zip_code_prefix = Column(String(10))
    seller_city = Column(String(100))
    seller_state = Column(String(2))

    order_items = relationship("OrderItem", back_populates="seller")


class ProductCategory(Base):
    __tablename__ = "product_categories"

    product_category_name = Column(String(100), primary_key=True)
    product_category_name_english = Column(String(100))


class Product(Base):
    __tablename__ = "products"

    product_id = Column(String(50), primary_key=True)
    product_category_name = Column(String(100))
    product_name_lenght = Column(Integer)  # typo original del dataset
    product_description_lenght = Column(Integer)  # typo original del dataset
    product_photos_qty = Column(Integer)
    product_weight_g = Column(Integer)
    product_length_cm = Column(Integer)
    product_height_cm = Column(Integer)
    product_width_cm = Column(Integer)

    order_items = relationship("OrderItem", back_populates="product")


class Order(Base):
    __tablename__ = "orders"

    order_id = Column(String(50), primary_key=True)
    customer_id = Column(String(50), ForeignKey("customers.customer_id"))
    order_status = Column(String(20))
    order_purchase_timestamp = Column(TIMESTAMP)
    order_approved_at = Column(TIMESTAMP)
    order_delivered_carrier_date = Column(TIMESTAMP)
    order_delivered_customer_date = Column(TIMESTAMP)
    order_estimated_delivery_date = Column(TIMESTAMP)

    customer = relationship("Customer", back_populates="orders")
    items = relationship("OrderItem", back_populates="order")
    payments = relationship("OrderPayment", back_populates="order")
    reviews = relationship("OrderReview", back_populates="order")


class OrderItem(Base):
    __tablename__ = "order_items"

    order_id = Column(String(50), ForeignKey("orders.order_id"), primary_key=True)
    order_item_id = Column(Integer, primary_key=True)
    product_id = Column(String(50), ForeignKey("products.product_id"))
    seller_id = Column(String(50), ForeignKey("sellers.seller_id"))
    shipping_limit_date = Column(TIMESTAMP)
    price = Column(Numeric(10, 2))
    freight_value = Column(Numeric(10, 2))

    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")
    seller = relationship("Seller", back_populates="order_items")


class OrderPayment(Base):
    __tablename__ = "order_payments"

    order_id = Column(String(50), ForeignKey("orders.order_id"), primary_key=True)
    payment_sequential = Column(Integer, primary_key=True)
    payment_type = Column(String(20))
    payment_installments = Column(Integer)
    payment_value = Column(Numeric(10, 2))

    order = relationship("Order", back_populates="payments")


class OrderReview(Base):
    __tablename__ = "order_reviews"

    review_id = Column(String(50), primary_key=True)
    order_id = Column(String(50), ForeignKey("orders.order_id"))
    review_score = Column(Integer)
    review_comment_title = Column(Text)
    review_comment_message = Column(Text)
    review_creation_date = Column(TIMESTAMP)
    review_answer_timestamp = Column(TIMESTAMP)

    order = relationship("Order", back_populates="reviews")


class QueryLog(Base):
    __tablename__ = "query_logs"

    id = Column(Integer, primary_key=True, index=True)
    pregunta_usuario = Column(Text, nullable=False)
    query_generada = Column(Text)
    respuesta = Column(Text)
    exitosa = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
