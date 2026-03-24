import { useState, useEffect } from 'react';
import { Users, Trophy, MapPin } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { obtenerCustomers, obtenerCustomersPorEstado, obtenerTopSpenders, obtenerCiudades } from '../api';
import { formatCurrency, formatNumber } from '../utils/formatters';

function Customers() {
  const [customers, setCustomers] = useState([]);
  const [customersPorEstado, setCustomersPorEstado] = useState([]);
  const [topSpenders, setTopSpenders] = useState([]);
  const [ciudades, setCiudades] = useState([]);
  const [loading, setLoading] = useState(true);
  const [vista, setVista] = useState('estados');

  useEffect(() => {
    const cargarDatos = async () => {
      try {
        const [customersData, estadosData, topData, ciudadesData] = await Promise.all([
          obtenerCustomers(30),
          obtenerCustomersPorEstado(),
          obtenerTopSpenders(10),
          obtenerCiudades(15)
        ]);
        setCustomers(customersData);
        setCustomersPorEstado(estadosData);
        setTopSpenders(topData);
        setCiudades(ciudadesData);
      } catch (error) {
        console.error('Error cargando customers:', error);
      } finally {
        setLoading(false);
      }
    };
    cargarDatos();
  }, []);

  if (loading) {
    return <div className="text-white text-xl">Cargando clientes...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-white flex items-center gap-3">
            <Users className="text-blue-400" />
            Clientes
          </h1>
          <p className="text-gray-400 mt-1">~99,000 clientes de todo Brasil</p>
        </div>

        <div className="flex gap-2">
          <button
            onClick={() => setVista('estados')}
            className={`px-4 py-2 rounded-lg transition-colors flex items-center gap-2 ${
              vista === 'estados' ? 'bg-blue-600 text-white' : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
            }`}
          >
            <MapPin size={16} />
            Por Estado
          </button>
          <button
            onClick={() => setVista('top')}
            className={`px-4 py-2 rounded-lg transition-colors flex items-center gap-2 ${
              vista === 'top' ? 'bg-yellow-600 text-white' : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
            }`}
          >
            <Trophy size={16} />
            Top Spenders
          </button>
        </div>
      </div>

      {vista === 'estados' ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Grafico por estado */}
          <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
            <h2 className="text-xl font-semibold text-white mb-4">Clientes por Estado</h2>
            <ResponsiveContainer width="100%" height={400}>
              <BarChart data={customersPorEstado.slice(0, 15)} layout="vertical">
                <XAxis type="number" stroke="#9CA3AF" />
                <YAxis type="category" dataKey="state" stroke="#9CA3AF" width={40} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#1F2937', border: '1px solid #374151' }}
                  formatter={(value) => [formatNumber(value), 'Clientes']}
                />
                <Bar dataKey="count" fill="#3B82F6" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Ciudades principales */}
          <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
            <h2 className="text-xl font-semibold text-white mb-4">Ciudades Principales</h2>
            <div className="space-y-3">
              {ciudades.map((ciudad) => (
                <div key={`${ciudad.city}-${ciudad.state}`} className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <span className="text-gray-500 w-6">{ciudades.indexOf(ciudad) + 1}.</span>
                    <div>
                      <p className="text-white">{ciudad.city}</p>
                      <p className="text-gray-500 text-sm">{ciudad.state}</p>
                    </div>
                  </div>
                  <span className="text-blue-400 font-medium">{formatNumber(ciudad.count)}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      ) : (
        <div className="grid gap-4">
          {topSpenders.map((customer) => (
            <div key={customer.customer_id} className="bg-gray-800 rounded-xl border border-gray-700 p-6 flex items-center gap-4">
              <div className={`w-12 h-12 rounded-full flex items-center justify-center text-xl font-bold ${
                topSpenders.indexOf(customer) === 0 ? 'bg-yellow-500 text-yellow-900' :
                topSpenders.indexOf(customer) === 1 ? 'bg-gray-400 text-gray-800' :
                topSpenders.indexOf(customer) === 2 ? 'bg-orange-600 text-orange-100' :
                'bg-gray-600 text-gray-300'
              }`}>
                {topSpenders.indexOf(customer) + 1}
              </div>

              <div className="flex-1">
                <h3 className="text-white font-semibold">Cliente {customer.customer_id}</h3>
                <p className="text-gray-400">{customer.city}, {customer.state}</p>
              </div>

              <div className="text-right">
                <p className="text-2xl font-bold text-green-400">{formatCurrency(customer.total_spent)}</p>
                <p className="text-gray-400 text-sm">{customer.total_orders} pedidos</p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default Customers;
