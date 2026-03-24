import { useState, useEffect } from 'react';
import { Store, TrendingUp, Star, MapPin } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { obtenerSellers, obtenerSellersPorEstado, obtenerTopSellers, obtenerBestRatedSellers } from '../api';

function Sellers() {
  const [sellers, setSellers] = useState([]);
  const [sellersPorEstado, setSellersPorEstado] = useState([]);
  const [topSellers, setTopSellers] = useState([]);
  const [bestRated, setBestRated] = useState([]);
  const [loading, setLoading] = useState(true);
  const [vista, setVista] = useState('top');

  useEffect(() => {
    const cargarDatos = async () => {
      try {
        const [sellersData, estadosData, topData, ratedData] = await Promise.all([
          obtenerSellers(30),
          obtenerSellersPorEstado(),
          obtenerTopSellers(10),
          obtenerBestRatedSellers(10)
        ]);
        setSellers(sellersData);
        setSellersPorEstado(estadosData);
        setTopSellers(topData);
        setBestRated(ratedData);
      } catch (error) {
        console.error('Error cargando sellers:', error);
      } finally {
        setLoading(false);
      }
    };
    cargarDatos();
  }, []);

  if (loading) {
    return <div className="text-white text-xl">Cargando vendedores...</div>;
  }

  const formatCurrency = (value) => `R$ ${value.toLocaleString()}`;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-white flex items-center gap-3">
            <Store className="text-orange-400" />
            Vendedores
          </h1>
          <p className="text-gray-400 mt-1">~3,000 vendedores en la plataforma</p>
        </div>

        <div className="flex gap-2">
          <button
            onClick={() => setVista('top')}
            className={`px-4 py-2 rounded-lg transition-colors flex items-center gap-2 ${
              vista === 'top' ? 'bg-orange-600 text-white' : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
            }`}
          >
            <TrendingUp size={16} />
            Top Ventas
          </button>
          <button
            onClick={() => setVista('rating')}
            className={`px-4 py-2 rounded-lg transition-colors flex items-center gap-2 ${
              vista === 'rating' ? 'bg-yellow-600 text-white' : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
            }`}
          >
            <Star size={16} />
            Mejor Valorados
          </button>
          <button
            onClick={() => setVista('estados')}
            className={`px-4 py-2 rounded-lg transition-colors flex items-center gap-2 ${
              vista === 'estados' ? 'bg-blue-600 text-white' : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
            }`}
          >
            <MapPin size={16} />
            Por Estado
          </button>
        </div>
      </div>

      {vista === 'top' && (
        <div className="grid gap-4">
          {topSellers.map((seller, index) => (
            <div key={index} className="bg-gray-800 rounded-xl border border-gray-700 p-6 flex items-center gap-4">
              <div className={`w-12 h-12 rounded-full flex items-center justify-center text-xl font-bold ${
                index === 0 ? 'bg-yellow-500 text-yellow-900' :
                index === 1 ? 'bg-gray-400 text-gray-800' :
                index === 2 ? 'bg-orange-600 text-orange-100' :
                'bg-gray-600 text-gray-300'
              }`}>
                {index + 1}
              </div>

              <div className="flex-1">
                <h3 className="text-white font-semibold">Vendedor {seller.seller_id}</h3>
                <p className="text-gray-400">{seller.city}, {seller.state}</p>
              </div>

              <div className="text-right">
                <p className="text-2xl font-bold text-green-400">{formatCurrency(seller.total_revenue)}</p>
                <p className="text-gray-400 text-sm">{seller.total_orders} pedidos</p>
              </div>
            </div>
          ))}
        </div>
      )}

      {vista === 'rating' && (
        <div className="grid gap-4">
          {bestRated.map((seller, index) => (
            <div key={index} className="bg-gray-800 rounded-xl border border-gray-700 p-6 flex items-center gap-4">
              <div className="w-12 h-12 rounded-full bg-yellow-600 flex items-center justify-center">
                <Star size={24} className="text-white" />
              </div>

              <div className="flex-1">
                <h3 className="text-white font-semibold">Vendedor {seller.seller_id}</h3>
                <p className="text-gray-400">{seller.city}, {seller.state}</p>
              </div>

              <div className="text-right">
                <div className="flex items-center gap-1 justify-end">
                  <Star size={20} className="text-yellow-400 fill-yellow-400" />
                  <span className="text-2xl font-bold text-white">{seller.avg_score}</span>
                </div>
                <p className="text-gray-400 text-sm">{seller.total_reviews} reviews</p>
              </div>
            </div>
          ))}
        </div>
      )}

      {vista === 'estados' && (
        <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
          <h2 className="text-xl font-semibold text-white mb-4">Vendedores por Estado</h2>
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={sellersPorEstado.slice(0, 15)} layout="vertical">
              <XAxis type="number" stroke="#9CA3AF" />
              <YAxis type="category" dataKey="state" stroke="#9CA3AF" width={40} />
              <Tooltip
                contentStyle={{ backgroundColor: '#1F2937', border: '1px solid #374151' }}
                formatter={(value) => [value.toLocaleString(), 'Vendedores']}
              />
              <Bar dataKey="count" fill="#F59E0B" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}

export default Sellers;
