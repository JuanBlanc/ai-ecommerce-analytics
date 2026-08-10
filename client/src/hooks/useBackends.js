import { useState, useEffect, useCallback } from 'react';
import { obtenerModelos } from '../api';

/**
 * Carga los backends de IA disponibles y los modelos que expone cada uno.
 *
 * Ollama puede arrancar despues que la API (el CORE lo re-detecta cada 30s),
 * asi que el hook expone `recargar` para volver a pedir la lista sin recargar
 * la pagina.
 */
export function useBackends() {
  const [backends, setBackends] = useState([]);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState(null);

  const cargar = useCallback(async () => {
    setCargando(true);
    setError(null);
    try {
      setBackends(await obtenerModelos());
    } catch (err) {
      setBackends([]);
      setError(err.message || 'No se pudieron cargar los modelos disponibles.');
    } finally {
      setCargando(false);
    }
  }, []);

  useEffect(() => {
    cargar();
  }, [cargar]);

  return { backends, cargando, error, recargar: cargar };
}
