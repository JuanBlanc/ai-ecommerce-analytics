// Funciones de formateo reutilizables

/**
 * Formatea un valor como moneda brasilena (BRL).
 */
export const formatCurrency = (value, currency = 'BRL') => {
  if (value === null || value === undefined) return 'R$ 0';
  return new Intl.NumberFormat('es-ES', {
    style: 'currency',
    currency,
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  }).format(value);
};

/**
 * Formatea un numero con separadores de miles.
 */
export const formatNumber = (value) => {
  if (value === null || value === undefined) return '0';
  return value.toLocaleString();
};

/**
 * Formatea una fecha en formato legible.
 */
export const formatDate = (dateStr, locale = 'es-ES') => {
  if (!dateStr) return '-';
  return new Date(dateStr).toLocaleDateString(locale);
};
