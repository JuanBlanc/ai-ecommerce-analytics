// Cliente API usando fetch nativo (sin dependencias externas)

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Extrae el mensaje de error de la API (FastAPI lo manda en `detail`)
async function extraerError(response) {
  try {
    const cuerpo = await response.json();
    if (cuerpo?.detail) {
      return typeof cuerpo.detail === 'string' ? cuerpo.detail : JSON.stringify(cuerpo.detail);
    }
  } catch {
    // La respuesta no traia JSON; se usa el mensaje generico de abajo
  }
  return `Error ${response.status}`;
}

// Funcion auxiliar para peticiones GET
async function get(endpoint) {
  const response = await fetch(`${API_URL}${endpoint}`);
  if (!response.ok) throw new Error(await extraerError(response));
  return response.json();
}

// Funcion auxiliar para peticiones POST
async function post(endpoint, data) {
  const response = await fetch(`${API_URL}${endpoint}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  if (!response.ok) throw new Error(await extraerError(response));
  return response.json();
}

// === CHATBOT ===
// `backend` y `modelo` son opcionales: sin ellos el CORE usa su cadena automatica.
// El modelo solo se envia junto al backend, la API lo rechaza suelto.
export const enviarPregunta = (pregunta, backend = null, modelo = null) => {
  const payload = { pregunta };
  if (backend) {
    payload.backend = backend;
    if (modelo) payload.modelo = modelo;
  }
  return post('/chat/', payload);
};
export const obtenerModelos = () => get('/chat/modelos');
export const obtenerHistorial = () => get('/chat/historial');

// === ESTADISTICAS ===
export const obtenerEstadisticas = () => get('/estadisticas/');
export const obtenerRevenueCategoria = () => get('/estadisticas/revenue-by-category');
export const obtenerRevenueEstado = () => get('/estadisticas/revenue-by-state');
export const obtenerMetodosPago = () => get('/estadisticas/payment-methods');
export const obtenerTendenciasMensuales = () => get('/estadisticas/monthly-trends');

// === ORDERS ===
export const obtenerOrders = (status = null, limit = 50) => {
  const params = new URLSearchParams({ limit });
  if (status) params.append('status', status);
  return get(`/orders/?${params}`);
};
export const obtenerOrdersPorEstado = () => get('/orders/by-status');
export const obtenerOrdersMensuales = (year = 2018) => get(`/orders/monthly?year=${year}`);

// === CUSTOMERS ===
export const obtenerCustomers = (limit = 50) => get(`/customers/?limit=${limit}`);
export const obtenerCustomersPorEstado = () => get('/customers/by-state');
export const obtenerTopSpenders = (limit = 10) => get(`/customers/top-spenders?limit=${limit}`);
export const obtenerCiudades = (limit = 20) => get(`/customers/cities?limit=${limit}`);

// === PRODUCTS ===
export const obtenerProducts = (limit = 50) => get(`/products/?limit=${limit}`);
export const obtenerCategorias = () => get('/products/categories');
export const obtenerProductosPorCategoria = () => get('/products/by-category');
export const obtenerTopSelling = (limit = 10) => get(`/products/top-selling?limit=${limit}`);

// === SELLERS ===
export const obtenerSellers = (limit = 50) => get(`/sellers/?limit=${limit}`);
export const obtenerSellersPorEstado = () => get('/sellers/by-state');
export const obtenerTopSellers = (limit = 10) => get(`/sellers/top-performers?limit=${limit}`);
export const obtenerBestRatedSellers = (limit = 10) => get(`/sellers/best-rated?limit=${limit}`);

// === REVIEWS ===
export const obtenerReviewsStats = () => get('/reviews/stats');
export const obtenerDistribucionReviews = () => get('/reviews/distribution');
export const obtenerReviewsNegativas = (limit = 20) => get(`/reviews/negative?limit=${limit}`);
export const obtenerReviewsPorCategoria = () => get('/reviews/by-category');
