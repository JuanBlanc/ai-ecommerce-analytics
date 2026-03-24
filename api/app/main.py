from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import orders, customers, products, sellers, reviews, estadisticas, chat

app = FastAPI(
    title="Olist E-Commerce API",
    description="API para análisis de datos de e-commerce brasileño con chatbot de consultas en lenguaje natural",
    version="2.0.0"
)

# CORS para permitir peticiones desde el frontend React
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(orders.router)
app.include_router(customers.router)
app.include_router(products.router)
app.include_router(sellers.router)
app.include_router(reviews.router)
app.include_router(estadisticas.router)
app.include_router(chat.router)


@app.get("/", tags=["Root"])
def root():
    """Endpoint raíz con información de la API"""
    return {
        "mensaje": "Olist E-Commerce API - Dataset brasileño con 100k+ pedidos",
        "version": "2.0.0",
        "docs": "/docs",
        "endpoints": {
            "orders": "/orders - Pedidos",
            "customers": "/customers - Clientes",
            "products": "/products - Productos",
            "sellers": "/sellers - Vendedores",
            "reviews": "/reviews - Valoraciones",
            "estadisticas": "/estadisticas - Métricas y análisis",
            "chat": "/chat - Chatbot IA"
        },
        "dataset": {
            "source": "Kaggle - Brazilian E-Commerce by Olist",
            "orders": "~100,000",
            "customers": "~99,000",
            "products": "~33,000",
            "sellers": "~3,000",
            "reviews": "~100,000"
        }
    }


@app.get("/health", tags=["Health"])
def health_check():
    """Health check para Docker"""
    return {"status": "healthy"}
