import { useState, useEffect } from 'react';
import { Star, ThumbsUp, ThumbsDown, BarChart3 } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { obtenerReviewsStats, obtenerDistribucionReviews, obtenerReviewsNegativas, obtenerReviewsPorCategoria } from '../api';

const COLORS = ['#EF4444', '#F97316', '#F59E0B', '#84CC16', '#10B981'];

function Reviews() {
  const [stats, setStats] = useState(null);
  const [distribucion, setDistribucion] = useState([]);
  const [negativas, setNegativas] = useState([]);
  const [porCategoria, setPorCategoria] = useState([]);
  const [loading, setLoading] = useState(true);
  const [vista, setVista] = useState('stats');

  useEffect(() => {
    const cargarDatos = async () => {
      try {
        const [statsData, distData, negData, catData] = await Promise.all([
          obtenerReviewsStats(),
          obtenerDistribucionReviews(),
          obtenerReviewsNegativas(15),
          obtenerReviewsPorCategoria()
        ]);
        setStats(statsData);
        setDistribucion(distData);
        setNegativas(negData);
        setPorCategoria(catData);
      } catch (error) {
        console.error('Error cargando reviews:', error);
      } finally {
        setLoading(false);
      }
    };
    cargarDatos();
  }, []);

  if (loading) {
    return <div className="text-white text-xl">Cargando reviews...</div>;
  }

  const renderStars = (score) => {
    return Array.from({ length: 5 }, (_, i) => (
      <Star
        key={i}
        size={16}
        className={i < score ? 'text-yellow-400 fill-yellow-400' : 'text-gray-600'}
      />
    ));
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-white flex items-center gap-3">
            <Star className="text-yellow-400" />
            Reviews
          </h1>
          <p className="text-gray-400 mt-1">~100,000 valoraciones de clientes</p>
        </div>

        <div className="flex gap-2">
          <button
            onClick={() => setVista('stats')}
            className={`px-4 py-2 rounded-lg transition-colors flex items-center gap-2 ${
              vista === 'stats' ? 'bg-yellow-600 text-white' : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
            }`}
          >
            <BarChart3 size={16} />
            Estadisticas
          </button>
          <button
            onClick={() => setVista('negativas')}
            className={`px-4 py-2 rounded-lg transition-colors flex items-center gap-2 ${
              vista === 'negativas' ? 'bg-red-600 text-white' : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
            }`}
          >
            <ThumbsDown size={16} />
            Negativas
          </button>
        </div>
      </div>

      {vista === 'stats' && (
        <>
          {/* Stats cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
              <p className="text-gray-400 text-sm">Total Reviews</p>
              <p className="text-3xl font-bold text-white mt-1">{stats?.total_reviews?.toLocaleString()}</p>
            </div>
            <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
              <p className="text-gray-400 text-sm">Puntuacion Media</p>
              <div className="flex items-center gap-2 mt-1">
                <Star size={24} className="text-yellow-400 fill-yellow-400" />
                <span className="text-3xl font-bold text-white">{stats?.avg_score}</span>
              </div>
            </div>
            <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
              <p className="text-gray-400 text-sm">Con Comentarios</p>
              <p className="text-3xl font-bold text-white mt-1">{stats?.with_comments?.toLocaleString()}</p>
            </div>
            <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
              <p className="text-gray-400 text-sm">Rango</p>
              <p className="text-3xl font-bold text-white mt-1">{stats?.min_score} - {stats?.max_score}</p>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Distribucion */}
            <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
              <h2 className="text-xl font-semibold text-white mb-4">Distribucion de Puntuaciones</h2>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={distribucion}>
                  <XAxis dataKey="score" stroke="#9CA3AF" />
                  <YAxis stroke="#9CA3AF" tickFormatter={(v) => `${(v/1000).toFixed(0)}k`} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#1F2937', border: '1px solid #374151' }}
                    formatter={(value) => [value.toLocaleString(), 'Reviews']}
                  />
                  <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                    {distribucion.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[entry.score - 1]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Por categoria */}
            <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
              <h2 className="text-xl font-semibold text-white mb-4">Puntuacion por Categoria</h2>
              <div className="space-y-3">
                {porCategoria.slice(0, 10).map((cat, index) => (
                  <div key={index} className="flex items-center justify-between">
                    <span className="text-white text-sm truncate max-w-[200px]">{cat.category || 'N/A'}</span>
                    <div className="flex items-center gap-2">
                      <div className="flex">{renderStars(Math.round(cat.avg_score))}</div>
                      <span className="text-yellow-400 font-medium w-10 text-right">{cat.avg_score}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </>
      )}

      {vista === 'negativas' && (
        <div className="space-y-4">
          <p className="text-gray-400">Reviews con puntuacion 1-2 estrellas y comentario:</p>
          {negativas.map((review, index) => (
            <div key={index} className="bg-gray-800 rounded-xl border border-gray-700 p-6">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <div className="flex">{renderStars(review.score)}</div>
                  <span className="text-red-400 font-medium">{review.score}/5</span>
                </div>
                <span className="text-gray-500 text-sm">
                  {review.date ? new Date(review.date).toLocaleDateString('es-ES') : '-'}
                </span>
              </div>
              <p className="text-gray-300">{review.message || 'Sin comentario'}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default Reviews;
