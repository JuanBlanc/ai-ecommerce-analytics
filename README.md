# Olist E-Commerce Dashboard

Sistema de analisis de datos de e-commerce brasileno con chatbot de consultas en lenguaje natural.

**Dataset**: [Brazilian E-Commerce by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) - 100k+ pedidos reales (2016-2018)

## Arquitectura

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Client    │────▶│     API     │────▶│  PostgreSQL │
│   (React)   │     │  (FastAPI)  │     │     (DB)    │
└─────────────┘     └──────┬──────┘     └─────────────┘
                          │
                          ▼
                   ┌─────────────┐
                   │    CORE     │
                   │  (NLP/IA)   │
                   └─────────────┘
```

## Dataset Olist

| Tabla | Registros | Descripcion |
|-------|-----------|-------------|
| orders | ~100,000 | Pedidos con estado y fechas |
| order_items | ~113,000 | Items de cada pedido |
| customers | ~99,000 | Clientes unicos |
| products | ~33,000 | Catalogo de productos |
| sellers | ~3,000 | Vendedores |
| order_payments | ~104,000 | Metodos de pago |
| order_reviews | ~100,000 | Valoraciones con texto |
| geolocation | ~1,000,000 | Coordenadas por CP |

## Requisitos

- Docker y Docker Compose
- Dataset de Kaggle (descarga manual)

## Instalacion

### 1. Descargar dataset

1. Ve a [Kaggle Olist Dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)
2. Descarga y descomprime
3. Copia los CSVs a la carpeta `data/`:

```
carlos/
└── data/
    ├── olist_customers_dataset.csv
    ├── olist_orders_dataset.csv
    ├── olist_order_items_dataset.csv
    ├── olist_order_payments_dataset.csv
    ├── olist_order_reviews_dataset.csv
    ├── olist_products_dataset.csv
    ├── olist_sellers_dataset.csv
    ├── olist_geolocation_dataset.csv
    └── product_category_name_translation.csv
```

### 2. Arrancar servicios

```bash
docker-compose up --build
```

### 3. Importar datos

```bash
docker exec -it empresa_api python -m app.import_data
```

## URLs

| Servicio | URL |
|----------|-----|
| Frontend React | http://localhost:3000 |
| API FastAPI | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |
| CORE NLP | http://localhost:8001 |

## Chatbot IA

Preguntas que entiende el sistema:

**Estadisticas:**
- "Dame las estadisticas generales"
- "Cual es el total facturado?"
- "Tendencias mensuales de ventas"

**Pedidos:**
- "Cuantos pedidos estan entregados?"
- "Pedidos cancelados"
- "Rendimiento de entregas"

**Clientes:**
- "Quienes son los mejores clientes?"
- "Clientes por estado"
- "Ciudades con mas clientes"

**Productos:**
- "Categorias mas vendidas"
- "Productos por categoria"
- "Revenue por categoria"

**Vendedores:**
- "Top 10 vendedores"
- "Vendedores mejor valorados"
- "Vendedores por estado"

**Reviews:**
- "Distribucion de reviews"
- "Reviews negativas"
- "Puntuacion media"

**Pagos:**
- "Metodos de pago utilizados"

## Estructura del proyecto

```
carlos/
├── docker-compose.yml
├── .env
├── data/                    # CSVs de Kaggle (crear)
├── api/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── main.py
│       ├── database.py
│       ├── models.py
│       ├── schemas.py
│       ├── import_data.py   # Script de importacion
│       └── routers/
│           ├── orders.py
│           ├── customers.py
│           ├── products.py
│           ├── sellers.py
│           ├── reviews.py
│           ├── estadisticas.py
│           └── chat.py
├── core/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── src/
│       ├── main.py
│       └── engine.py        # Motor NLP
├── client/
│   ├── Dockerfile
│   ├── package.json
│   └── src/
│       ├── App.jsx
│       ├── api.js
│       └── pages/
│           ├── Dashboard.jsx
│           ├── Chat.jsx
│           ├── Orders.jsx
│           ├── Customers.jsx
│           ├── Products.jsx
│           ├── Sellers.jsx
│           └── Reviews.jsx
└── db/
    └── init.sql
```

## Tecnologias

- **Backend**: Python 3.11, FastAPI, SQLAlchemy, Pydantic, Pandas
- **Frontend**: React 18, Vite, Tailwind CSS, Recharts, Lucide Icons
- **Base de datos**: PostgreSQL 15
- **Infraestructura**: Docker, Docker Compose

## API Endpoints

### Orders
- `GET /orders/` - Listar pedidos
- `GET /orders/by-status` - Pedidos por estado
- `GET /orders/by-state` - Pedidos por estado geografico
- `GET /orders/monthly` - Pedidos mensuales

### Customers
- `GET /customers/` - Listar clientes
- `GET /customers/by-state` - Clientes por estado
- `GET /customers/top-spenders` - Mejores compradores
- `GET /customers/cities` - Ciudades principales

### Products
- `GET /products/` - Listar productos
- `GET /products/categories` - Categorias
- `GET /products/top-selling` - Mas vendidos
- `GET /products/category-revenue` - Revenue por categoria

### Sellers
- `GET /sellers/` - Listar vendedores
- `GET /sellers/by-state` - Por estado
- `GET /sellers/top-performers` - Top vendedores
- `GET /sellers/best-rated` - Mejor valorados

### Reviews
- `GET /reviews/` - Listar reviews
- `GET /reviews/stats` - Estadisticas
- `GET /reviews/distribution` - Distribucion
- `GET /reviews/negative` - Reviews negativas

### Estadisticas
- `GET /estadisticas/` - Estadisticas generales
- `GET /estadisticas/revenue-by-state` - Por estado
- `GET /estadisticas/revenue-by-category` - Por categoria
- `GET /estadisticas/payment-methods` - Metodos de pago
- `GET /estadisticas/monthly-trends` - Tendencias

### Chat
- `POST /chat/` - Enviar pregunta
- `GET /chat/historial` - Historial
