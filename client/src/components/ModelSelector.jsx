import { useEffect } from 'react';
import { Cpu, RefreshCw, AlertCircle } from 'lucide-react';

// El value del select combina backend y modelo porque dos backends pueden
// ofrecer el mismo nombre de modelo.
const VALOR_AUTOMATICO = '';
const SEPARADOR = '::';

/**
 * Selector del backend y modelo con el que generar el SQL.
 * Ollama lista todos los modelos instalados en el host; Claude y el backend
 * compatible con OpenAI listan los suyos si hay API key configurada.
 */
function ModelSelector({ backends, cargando, error, onRecargar, seleccion, onSeleccionar }) {
  const disponibles = backends.filter((backend) => backend.disponible && backend.modelos.length > 0);
  const noDisponibles = backends.filter(
    (backend) => !backend.disponible || backend.modelos.length === 0
  );

  // Si Ollama se cae o cambia de modelos, la seleccion previa deja de existir:
  // se vuelve a la cadena automatica en lugar de mandar algo que dara 400.
  useEffect(() => {
    if (!seleccion.backend || cargando) return;

    const sigueValido = disponibles.some(
      (backend) => backend.id === seleccion.backend && backend.modelos.includes(seleccion.modelo)
    );
    if (!sigueValido) onSeleccionar({ backend: null, modelo: null });
  }, [disponibles, seleccion, cargando, onSeleccionar]);

  const manejarCambio = (event) => {
    const valor = event.target.value;

    if (valor === VALOR_AUTOMATICO) {
      onSeleccionar({ backend: null, modelo: null });
      return;
    }

    const [backend, modelo] = valor.split(SEPARADOR);
    onSeleccionar({ backend, modelo });
  };

  const valorActual = seleccion.backend
    ? `${seleccion.backend}${SEPARADOR}${seleccion.modelo}`
    : VALOR_AUTOMATICO;

  return (
    <div className="flex items-center gap-2 flex-wrap">
      <label className="text-gray-400 text-xs flex items-center gap-1.5">
        <Cpu size={14} />
        Modelo:
      </label>

      <select
        value={valorActual}
        onChange={manejarCambio}
        disabled={cargando}
        className="bg-gray-700 text-gray-200 text-xs rounded-lg px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-green-500 disabled:opacity-50 max-w-xs"
      >
        <option value={VALOR_AUTOMATICO}>Automático (Ollama › Claude › OpenAI)</option>

        {disponibles.map((backend) => (
          <optgroup key={backend.id} label={backend.nombre}>
            {backend.modelos.map((modelo) => (
              <option key={`${backend.id}-${modelo}`} value={`${backend.id}${SEPARADOR}${modelo}`}>
                {modelo}
              </option>
            ))}
          </optgroup>
        ))}

        {noDisponibles.map((backend) => (
          <option key={backend.id} disabled>
            {backend.nombre} — no disponible
          </option>
        ))}
      </select>

      <button
        type="button"
        onClick={onRecargar}
        disabled={cargando}
        title="Volver a buscar modelos disponibles"
        className="text-gray-400 hover:text-gray-200 disabled:opacity-50 transition-colors"
      >
        <RefreshCw size={14} className={cargando ? 'animate-spin' : ''} />
      </button>

      {error && (
        <span className="text-red-400 text-xs flex items-center gap-1">
          <AlertCircle size={12} />
          {error}
        </span>
      )}

      {!error && !cargando && disponibles.length === 0 && (
        <span className="text-yellow-400 text-xs flex items-center gap-1">
          <AlertCircle size={12} />
          Sin backends de IA configurados
        </span>
      )}
    </div>
  );
}

export default ModelSelector;
