import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Chatbot
export const enviarPregunta = async (pregunta) => {
  const response = await api.post('/chat/', { pregunta });
  return response.data;
};

export const obtenerHistorial = async () => {
  const response = await api.get('/chat/historial');
  return response.data;
};

// Estadísticas
export const obtenerEstadisticas = async () => {
  const response = await api.get('/estadisticas/');
  return response.data;
};

export const obtenerRevenueCategoria = async () => {
  const response = await api.get('/estadisticas/revenue-by-category');
  return response.data;
};

export const obtenerRevenueEstado = async () => {
  const response = await api.get('/estadisticas/revenue-by-state');
  return response.data;
};

export const obtenerMetodosPago = async () => {
  const response = await api.get('/estadisticas/payment-methods');
  return response.data;
};

export const obtenerTendenciasMensuales = async () => {
  const response = await api.get('/estadisticas/monthly-trends');
  return response.data;
};

// Orders
export const obtenerOrders = async (status = null, limit = 50) => {
  const params = new URLSearchParams();
  if (status) params.append('status', status);
  params.append('limit', limit);
  const response = await api.get(`/orders/?${params}`);
  return response.data;
};

export const obtenerOrdersPorEstado = async () => {
  const response = await api.get('/orders/by-status');
  return response.data;
};

export const obtenerOrdersMensuales = async (year = 2018) => {
  const response = await api.get(`/orders/monthly?year=${year}`);
  return response.data;
};

// Customers
export const obtenerCustomers = async (limit = 50) => {
  const response = await api.get(`/customers/?limit=${limit}`);
  return response.data;
};

export const obtenerCustomersPorEstado = async () => {
  const response = await api.get('/customers/by-state');
  return response.data;
};

export const obtenerTopSpenders = async (limit = 10) => {
  const response = await api.get(`/customers/top-spenders?limit=${limit}`);
  return response.data;
};

export const obtenerCiudades = async (limit = 20) => {
  const response = await api.get(`/customers/cities?limit=${limit}`);
  return response.data;
};

// Products
export const obtenerProducts = async (limit = 50) => {
  const response = await api.get(`/products/?limit=${limit}`);
  return response.data;
};

export const obtenerCategorias = async () => {
  const response = await api.get('/products/categories');
  return response.data;
};

export const obtenerProductosPorCategoria = async () => {
  const response = await api.get('/products/by-category');
  return response.data;
};

export const obtenerTopSelling = async (limit = 10) => {
  const response = await api.get(`/products/top-selling?limit=${limit}`);
  return response.data;
};

// Sellers
export const obtenerSellers = async (limit = 50) => {
  const response = await api.get(`/sellers/?limit=${limit}`);
  return response.data;
};

export const obtenerSellersPorEstado = async () => {
  const response = await api.get('/sellers/by-state');
  return response.data;
};

export const obtenerTopSellers = async (limit = 10) => {
  const response = await api.get(`/sellers/top-performers?limit=${limit}`);
  return response.data;
};

export const obtenerBestRatedSellers = async (limit = 10) => {
  const response = await api.get(`/sellers/best-rated?limit=${limit}`);
  return response.data;
};

// Reviews
export const obtenerReviewsStats = async () => {
  const response = await api.get('/reviews/stats');
  return response.data;
};

export const obtenerDistribucionReviews = async () => {
  const response = await api.get('/reviews/distribution');
  return response.data;
};

export const obtenerReviewsNegativas = async (limit = 20) => {
  const response = await api.get(`/reviews/negative?limit=${limit}`);
  return response.data;
};

export const obtenerReviewsPorCategoria = async () => {
  const response = await api.get('/reviews/by-category');
  return response.data;
};

export default api;
