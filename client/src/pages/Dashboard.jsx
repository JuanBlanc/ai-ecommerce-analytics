import { useState, useEffect } from 'react';
import { ShoppingCart, Users, Package, Store, DollarSign, Star, TrendingUp, XCircle } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line } from 'recharts';
import { obtenerEstadisticas, obtenerRevenueCategoria, obtenerOrdersPorEstado, obtenerTendenciasMensuales } from '../api';

function StatCard({ title, value, icon: Icon, color, subtitle }) {
  return (
    <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-gray-400 text-sm">{title}</p>
          <p className="text-2xl font-bold text-white mt-1">{value}</p>
          {subtitle && <p className="text-gray-500 text-xs mt-1">{subtitle}</p>}
        </div>
        <div className={`p-3 rounded-lg ${color}`}>
          <Icon size={24} className="text-white" />
        </div>
      </div>
    </div>
  );
}

const COLORS = ['#10B981', '#3B82F6', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899'];

function Dashboard() {
  const [stats, setStats] = useState(null);
  const [revenueCategoria, setRevenueCategoria] = useState([]);
  const [ordersPorEstado, setOrdersPorEstado] = useState([]);
  const [tendencias, setTendencias] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const cargarDatos = async () => {
      try {
        const [statsData, revenueData, ordersData, tendenciasData] = await Promise.all([
          obtenerEstadisticas(),
          obtenerRevenueCategoria(),
          obtenerOrdersPorEstado(),
          obtenerTendenciasMensuales()
        ]);

        setStats(statsData);
        setRevenueCategoria(revenueData.slice(0, 8));
        setOrdersPorEstado(ordersData);
        setTendencias(tendenciasData);
      } catch (err) {
        setError('Error al cargar datos. Verifica que la API esté corriendo y los datos importados.');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    cargarDatos();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-500 mx-auto"></div>
          <p className="text-white mt-4">Cargando datos de Olist...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-900/50 border border-red-500 rounded-xl p-6 text-red-200">
        <p className="font-bold mb-2">Error de conexion</p>
        <p>{error}</p>
        <p className="mt-4 text-sm">Asegurate de:</p>
        <ul className="list-disc list-inside text-sm mt-2">
          <li>Ejecutar: docker-compose up --build</li>
          <li>Importar datos: docker exec -it empresa_api python -m app.import_data</li>
        </ul>
      </div>
    );
  }

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('es-ES', {
      style: 'currency',
      currency: 'BRL',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value);
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-white">Dashboard Olist</h1>
        <p className="text-gray-400 mt-1">E-Commerce brasileno - Datos reales 2016-2018</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Pedidos"
          value={stats?.total_orders?.toLocaleString() || 0}
          icon={ShoppingCart}
          color="bg-green-600"
          subtitle={`${stats?.orders_delivered?.toLocaleString() || 0} entregados`}
        />
        <StatCard
          title="Clientes"
          value={stats?.total_customers?.toLocaleString() || 0}
          icon={Users}
          color="bg-blue-600"
        />
        <StatCard
          title="Productos"
          value={stats?.total_products?.toLocaleString() || 0}
          icon={Package}
          color="bg-purple-600"
        />
        <StatCard
          title="Vendedores"
          value={stats?.total_sellers?.toLocaleString() || 0}
          icon={Store}
          color="bg-orange-600"
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <StatCard
          title="Ingresos Totales"
          value={formatCurrency(stats?.total_revenue || 0)}
          icon={DollarSign}
          color="bg-emerald-600"
        />
        <StatCard
          title="Ticket Medio"
          value={formatCurrency(stats?.avg_order_value || 0)}
          icon={TrendingUp}
          color="bg-cyan-600"
        />
        <StatCard
          title="Puntuacion Media"
          value={`${stats?.avg_review_score || 0} / 5`}
          icon={Star}
          color="bg-yellow-600"
          subtitle={`${stats?.orders_canceled || 0} cancelados`}
        />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Tendencias Mensuales */}
        <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
          <h2 className="text-xl font-semibold text-white mb-4">Tendencia de Ventas</h2>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={tendencias}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="month" stroke="#9CA3AF" tick={{ fontSize: 10 }} />
              <YAxis stroke="#9CA3AF" tickFormatter={(v) => `${(v/1000).toFixed(0)}k`} />
              <Tooltip
                contentStyle={{ backgroundColor: '#1F2937', border: '1px solid #374151' }}
                labelStyle={{ color: '#fff' }}
                formatter={(value) => [formatCurrency(value), 'Ingresos']}
              />
              <Line type="monotone" dataKey="total_revenue" stroke="#10B981" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Pedidos por Estado */}
        <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
          <h2 className="text-xl font-semibold text-white mb-4">Pedidos por Estado</h2>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={ordersPorEstado}
                cx="50%"
                cy="50%"
                outerRadius={100}
                dataKey="count"
                nameKey="status"
                label={({ status, count }) => `${status}: ${count}`}
              >
                {ordersPorEstado.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip contentStyle={{ backgroundColor: '#1F2937', border: '1px solid #374151' }} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Revenue por Categoria */}
      <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
        <h2 className="text-xl font-semibold text-white mb-4">Ingresos por Categoria</h2>
        <ResponsiveContainer width="100%" height={350}>
          <BarChart data={revenueCategoria} layout="vertical">
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis type="number" stroke="#9CA3AF" tickFormatter={(v) => `${(v/1000).toFixed(0)}k`} />
            <YAxis type="category" dataKey="category" stroke="#9CA3AF" width={150} tick={{ fontSize: 11 }} />
            <Tooltip
              contentStyle={{ backgroundColor: '#1F2937', border: '1px solid #374151' }}
              formatter={(value) => [formatCurrency(value), 'Ingresos']}
            />
            <Bar dataKey="total_revenue" fill="#10B981" radius={[0, 4, 4, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export default Dashboard;
