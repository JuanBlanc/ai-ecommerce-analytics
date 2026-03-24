import { useState, useEffect } from 'react';
import { Star, ThumbsDown, BarChart3 } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { obtenerReviewsStats, obtenerDistribucionReviews, obtenerReviewsNegativas, obtenerReviewsPorCategoria } from '../api';
import { formatNumber, formatDate } from '../utils/formatters';
import { SCORE_COLORS } from '../utils/constants';
import { StarRating } from '../components/StarRating';

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
              <p className="text-3xl font-bold text-white mt-1">{formatNumber(stats?.total_reviews)}</p>
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
              <p className="text-3xl font-bold text-white mt-1">{formatNumber(stats?.with_comments)}</p>
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
                    formatter={(value) => [formatNumber(value), 'Reviews']}
                  />
                  <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                    {distribucion.map((entry) => (
                      <Cell key={`cell-${entry.score}`} fill={SCORE_COLORS[entry.score - 1]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Por categoria */}
            <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
              <h2 className="text-xl font-semibold text-white mb-4">Puntuacion por Categoria</h2>
              <div className="space-y-3">
                {porCategoria.slice(0, 10).map((cat) => (
                  <div key={cat.category || 'n-a'} className="flex items-center justify-between">
                    <span className="text-white text-sm truncate max-w-[200px]">{cat.category || 'N/A'}</span>
                    <div className="flex items-center gap-2">
                      <StarRating score={Math.round(cat.avg_score)} size={16} />
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
          {negativas.map((review) => (
            <div key={review.review_id || `${review.order_id}-${review.score}`} className="bg-gray-800 rounded-xl border border-gray-700 p-6">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <StarRating score={review.score} size={16} />
                  <span className="text-red-400 font-medium">{review.score}/5</span>
                </div>
                <span className="text-gray-500 text-sm">{formatDate(review.date)}</span>
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
