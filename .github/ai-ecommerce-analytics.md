---
title: Olist E-Commerce Dashboard
description: Analítica de 100.000 pedidos reales con un chatbot que consulta la base de datos en lenguaje natural.
slug: olist-dashboard
tags: [Python, FastAPI, React, PostgreSQL, LLM, Docker]
order: 1
---

Panel de analítica sobre el dataset público de Olist —más de 100.000 pedidos
reales de e-commerce brasileño entre 2016 y 2018, con sus clientes, productos,
vendedores, pagos y valoraciones— y encima una capa de consulta en lenguaje
natural: se pregunta «¿qué categorías se venden mejor?» y responde con datos
salidos de la base, no inventados.

## Cómo está montado

Tres piezas y una cuarta dentro de la API:

```
React (cliente)  ──▶  FastAPI  ──▶  PostgreSQL
                        │
                        └─▶  core/  ──▶  Claude · compatible OpenAI · Ollama
```

`api/app/core/` es un paquete independiente que la API importa. Recibe la
pregunta, devuelve el SQL, y cuando la API le pasa las filas ya consultadas
redacta el análisis. Lo que **no** hace es abrir la base de datos.

## La decisión que sostiene el proyecto

Que el módulo de IA no tenga conexión a Postgres no es una separación estética,
paga tres cosas:

- Cambiar de modelo —Claude, un backend compatible con OpenAI, un Ollama en la
  máquina— no toca ni una línea de la API. El cliente lo elige por petición y
  `GET /chat/modelos` dice qué hay disponible.
- La generación de consultas se puede probar sin levantar la base de datos: es
  una función de texto a texto.
- El modelo nunca sostiene una credencial ni una sesión abierta. Ejecutar es
  cosa de la API, que es quien decide qué se ejecuta.

## Lo demás que hay dentro

- Un router por dominio (`orders`, `customers`, `products`, `sellers`,
  `reviews`, `estadisticas`, `chat`), cada uno con sus agregados ya calculados
  en SQL en vez de en Python.
- La importación de los nueve CSV vive en su propio comando
  (`python -m app.import_data`) y no en el arranque: reconstruir la imagen no
  vuelve a ingerir el millón y medio de filas.
- Dashboard, chat y una vista por dominio en el cliente, con Recharts para las
  gráficas y Tailwind para el resto.

## Levantarlo

```bash
docker-compose up --build
docker exec -it empresa_api python -m app.import_data
```

Cliente en `:3000`, API en `:8000`, Swagger en `/docs` y `GET /health` dice qué
backend de IA está activo.

## Hasta dónde llega

Los CSV de Kaggle se descargan a mano —el dataset no se redistribuye— y el
chatbot responde bien dentro de las familias de preguntas para las que está
preparado; fuera de ellas contesta que no sabe en vez de improvisar un SQL.
