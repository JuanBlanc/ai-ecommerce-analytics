import { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Database, Sparkles, TrendingUp, Lightbulb, Cpu } from 'lucide-react';
import { BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { enviarPregunta } from '../api';
import { useBackends } from '../hooks/useBackends';
import ModelSelector from '../components/ModelSelector';
import { CHART_COLORS } from '../utils/constants';

// Preguntas de ejemplo para el chat
const EJEMPLOS = [
  "¿Cuáles son las ventas por estado?",
  "Top 10 categorías más vendidas",
  "¿Cómo es la distribución de métodos de pago?",
  "Tendencia mensual de ventas",
  "¿Cuáles son los vendedores con mejor rating?",
  "Reviews negativas del último mes",
  "¿Cuánto hemos facturado en total?",
  "Clientes que más han gastado",
];

function DynamicChart({ grafica, datos }) {
  if (!grafica || !datos || datos.length === 0) return null;

  const { tipo, x, y, titulo } = grafica;

  // Para gráfico de número único
  if (tipo === 'number' && datos.length > 0) {
    const valor = Object.values(datos[0])[0];
    return (
      <div className="bg-gray-900 rounded-lg p-6 text-center">
        <p className="text-gray-400 text-sm mb-2">{titulo}</p>
        <p className="text-4xl font-bold text-green-400">
          {typeof valor === 'number' ? valor.toLocaleString() : valor}
        </p>
      </div>
    );
  }

  // Para tabla
  if (tipo === 'table') {
    return null; // La tabla ya se renderiza por defecto
  }

  // Preparar datos para el gráfico
  const chartData = datos.slice(0, 15).map(item => {
    const newItem = { ...item };
    // Convertir valores numéricos
    Object.keys(newItem).forEach(key => {
      if (typeof newItem[key] === 'string' && !isNaN(newItem[key])) {
        newItem[key] = parseFloat(newItem[key]);
      }
    });
    return newItem;
  });

  // Detectar automáticamente x e y si no están definidos
  const keys = Object.keys(datos[0] || {});
  const xKey = x || keys[0];
  const yKey = y || keys.find(k => typeof datos[0][k] === 'number') || keys[1];

  return (
    <div className="bg-gray-900 rounded-lg p-4 mt-3">
      <p className="text-gray-400 text-sm mb-3 flex items-center gap-2">
        <TrendingUp size={14} />
        {titulo}
      </p>
      <ResponsiveContainer width="100%" height={250}>
        {tipo === 'bar' ? (
          <BarChart data={chartData} layout="vertical" margin={{ left: 80 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis type="number" stroke="#9CA3AF" tickFormatter={(v) => v >= 1000 ? `${(v/1000).toFixed(0)}k` : v} />
            <YAxis type="category" dataKey={xKey} stroke="#9CA3AF" tick={{ fontSize: 11 }} width={75} />
            <Tooltip
              contentStyle={{ backgroundColor: '#1F2937', border: '1px solid #374151' }}
              formatter={(value) => [typeof value === 'number' ? value.toLocaleString() : value]}
            />
            <Bar dataKey={yKey} fill="#10B981" radius={[0, 4, 4, 0]} />
          </BarChart>
        ) : tipo === 'line' ? (
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis dataKey={xKey} stroke="#9CA3AF" tick={{ fontSize: 10 }} />
            <YAxis stroke="#9CA3AF" tickFormatter={(v) => v >= 1000 ? `${(v/1000).toFixed(0)}k` : v} />
            <Tooltip
              contentStyle={{ backgroundColor: '#1F2937', border: '1px solid #374151' }}
              formatter={(value) => [typeof value === 'number' ? value.toLocaleString() : value]}
            />
            <Line type="monotone" dataKey={yKey} stroke="#10B981" strokeWidth={2} dot={false} />
          </LineChart>
        ) : tipo === 'pie' ? (
          <PieChart>
            <Pie
              data={chartData}
              cx="50%"
              cy="50%"
              outerRadius={80}
              dataKey={yKey}
              nameKey={xKey}
              label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
            >
              {chartData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={CHART_COLORS[index % CHART_COLORS.length]} />
              ))}
            </Pie>
            <Tooltip contentStyle={{ backgroundColor: '#1F2937', border: '1px solid #374151' }} />
          </PieChart>
        ) : null}
      </ResponsiveContainer>
    </div>
  );
}

function InsightsPanel({ insights }) {
  if (!insights || insights.length === 0) return null;

  return (
    <div className="bg-yellow-900/20 border border-yellow-700/50 rounded-lg p-3 mt-3">
      <p className="text-yellow-400 text-sm font-medium flex items-center gap-2 mb-2">
        <Lightbulb size={14} />
        Insights
      </p>
      <ul className="space-y-1">
        {insights.map((insight, i) => (
          <li key={i} className="text-yellow-200/80 text-sm flex items-start gap-2">
            <span className="text-yellow-500 mt-1">•</span>
            {insight}
          </li>
        ))}
      </ul>
    </div>
  );
}

function Chat() {
  const [mensajes, setMensajes] = useState([
    {
      tipo: 'bot',
      texto: '¡Hola! Soy el asistente IA de Olist. Puedo analizar los 100k+ pedidos del e-commerce brasileño y mostrarte gráficas con insights. ¿Qué quieres saber?',
      datos: null
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  // Sin backend elegido el CORE usa su cadena automatica
  const [seleccion, setSeleccion] = useState({ backend: null, modelo: null });
  const { backends, cargando, error: errorBackends, recargar } = useBackends();
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [mensajes]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const pregunta = input.trim();
    setInput('');

    setMensajes(prev => [...prev, { tipo: 'user', texto: pregunta }]);
    setLoading(true);

    try {
      const respuesta = await enviarPregunta(pregunta, seleccion.backend, seleccion.modelo);

      setMensajes(prev => [...prev, {
        tipo: 'bot',
        texto: respuesta.respuesta,
        datos: respuesta.datos,
        query: respuesta.query_sql,
        grafica: respuesta.grafica,
        insights: respuesta.insights,
        modeloUsado: respuesta.modelo_usado,
        exitosa: respuesta.exitosa
      }]);
    } catch (error) {
      setMensajes(prev => [...prev, {
        tipo: 'bot',
        texto: error.message || 'Error al procesar la pregunta. Verifica que los servicios estén corriendo y la API key configurada.',
        error: true
      }]);
    } finally {
      setLoading(false);
    }
  };

  const usarEjemplo = (ejemplo) => {
    setInput(ejemplo);
  };

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)]">
      <div className="mb-4">
        <h1 className="text-3xl font-bold text-white flex items-center gap-3">
          <Sparkles className="text-yellow-400" />
          Chatbot IA
        </h1>
        <p className="text-gray-400 mt-1">Consultas inteligentes con análisis y gráficas automáticas</p>
      </div>

      {/* Selector de backend y modelo */}
      <div className="mb-4">
        <ModelSelector
          backends={backends}
          cargando={cargando}
          error={errorBackends}
          onRecargar={recargar}
          seleccion={seleccion}
          onSeleccionar={setSeleccion}
        />
      </div>

      {/* Ejemplos */}
      <div className="mb-4">
        <p className="text-gray-400 text-sm mb-2">Ejemplos de preguntas:</p>
        <div className="flex flex-wrap gap-2">
          {EJEMPLOS.map((ejemplo, i) => (
            <button
              key={i}
              onClick={() => usarEjemplo(ejemplo)}
              className="text-xs bg-gray-700 hover:bg-gray-600 text-gray-300 px-3 py-1.5 rounded-full transition-colors"
            >
              {ejemplo}
            </button>
          ))}
        </div>
      </div>

      {/* Chat */}
      <div className="flex-1 bg-gray-800 rounded-xl border border-gray-700 overflow-hidden flex flex-col">
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {mensajes.map((msg, index) => (
            <div
              key={index}
              className={`flex gap-3 ${msg.tipo === 'user' ? 'flex-row-reverse' : ''}`}
            >
              <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                msg.tipo === 'user' ? 'bg-green-600' : 'bg-gradient-to-br from-blue-500 to-purple-600'
              }`}>
                {msg.tipo === 'user' ? <User size={16} /> : <Bot size={16} />}
              </div>

              <div className={`max-w-[80%] ${msg.tipo === 'user' ? 'text-right' : ''}`}>
                <div className={`rounded-xl px-4 py-3 ${
                  msg.tipo === 'user'
                    ? 'bg-green-600 text-white'
                    : msg.error
                      ? 'bg-red-900/50 text-red-200'
                      : 'bg-gray-700 text-gray-100'
                }`}>
                  <p className="whitespace-pre-wrap">{msg.texto}</p>
                </div>

                {/* Modelo que genero el SQL */}
                {msg.modeloUsado && (
                  <p className="text-gray-500 text-xs mt-1 flex items-center gap-1">
                    <Cpu size={11} />
                    {msg.modeloUsado}
                  </p>
                )}

                {/* Insights */}
                {msg.insights && <InsightsPanel insights={msg.insights} />}

                {/* Gráfica dinámica */}
                {msg.grafica && msg.datos && (
                  <DynamicChart grafica={msg.grafica} datos={msg.datos} />
                )}

                {/* Query SQL */}
                {msg.query && (
                  <div className="mt-2 bg-gray-900 rounded-lg p-3 text-xs">
                    <div className="flex items-center gap-2 text-gray-400 mb-1">
                      <Database size={12} />
                      <span>SQL generada por IA:</span>
                    </div>
                    <code className="text-green-400 whitespace-pre-wrap block max-h-24 overflow-auto">{msg.query}</code>
                  </div>
                )}

                {/* Tabla de datos */}
                {msg.datos && msg.datos.length > 0 && msg.grafica?.tipo !== 'number' && (
                  <div className="mt-2 bg-gray-900 rounded-lg p-3 overflow-x-auto max-h-64">
                    <p className="text-gray-400 text-xs mb-2">{msg.datos.length} resultados</p>
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="text-gray-400 border-b border-gray-700">
                          {Object.keys(msg.datos[0]).map((key) => (
                            <th key={key} className="text-left pb-2 px-2 whitespace-nowrap text-xs">{key}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {msg.datos.slice(0, 10).map((fila, i) => (
                          <tr key={i} className="border-b border-gray-800">
                            {Object.values(fila).map((valor, j) => (
                              <td key={j} className="py-1.5 px-2 text-gray-300 whitespace-nowrap text-xs">
                                {typeof valor === 'number'
                                  ? valor % 1 === 0 ? valor.toLocaleString() : valor.toFixed(2)
                                  : valor?.toString().substring(0, 40) || '-'}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                    {msg.datos.length > 10 && (
                      <p className="text-gray-500 text-xs mt-2">Mostrando 10 de {msg.datos.length}</p>
                    )}
                  </div>
                )}
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex gap-3">
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
                <Bot size={16} />
              </div>
              <div className="bg-gray-700 rounded-xl px-4 py-3 text-gray-300">
                <span className="animate-pulse flex items-center gap-2">
                  <Sparkles size={14} className="animate-spin" />
                  Analizando...
                </span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        <form onSubmit={handleSubmit} className="p-4 border-t border-gray-700">
          <div className="flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Pregunta sobre ventas, clientes, productos..."
              className="flex-1 bg-gray-700 text-white rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-green-500"
              disabled={loading}
            />
            <button
              type="submit"
              disabled={loading || !input.trim()}
              className="bg-green-600 hover:bg-green-700 disabled:bg-gray-600 text-white px-4 py-2 rounded-lg transition-colors"
            >
              <Send size={20} />
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default Chat;
