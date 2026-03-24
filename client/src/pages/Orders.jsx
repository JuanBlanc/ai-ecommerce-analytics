import { useState, useEffect } from 'react';
import { ShoppingCart, Clock, Truck, CheckCircle, XCircle, Package } from 'lucide-react';
import { obtenerOrders, obtenerOrdersPorEstado } from '../api';

const STATUS_CONFIG = {
  delivered: { label: 'Entregado', icon: CheckCircle, color: 'bg-green-600' },
  shipped: { label: 'Enviado', icon: Truck, color: 'bg-blue-600' },
  processing: { label: 'Procesando', icon: Package, color: 'bg-yellow-600' },
  canceled: { label: 'Cancelado', icon: XCircle, color: 'bg-red-600' },
  created: { label: 'Creado', icon: Clock, color: 'bg-gray-600' },
  invoiced: { label: 'Facturado', icon: Package, color: 'bg-purple-600' },
  unavailable: { label: 'No disponible', icon: XCircle, color: 'bg-orange-600' },
  approved: { label: 'Aprobado', icon: CheckCircle, color: 'bg-cyan-600' },
};

function Orders() {
  const [orders, setOrders] = useState([]);
  const [orderStats, setOrderStats] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filtro, setFiltro] = useState(null);

  useEffect(() => {
    const cargarDatos = async () => {
      setLoading(true);
      try {
        const [ordersData, statsData] = await Promise.all([
          obtenerOrders(filtro, 50),
          obtenerOrdersPorEstado()
        ]);
        setOrders(ordersData);
        setOrderStats(statsData);
      } catch (error) {
        console.error('Error cargando orders:', error);
      } finally {
        setLoading(false);
      }
    };
    cargarDatos();
  }, [filtro]);

  const getStatusConfig = (status) => STATUS_CONFIG[status] || STATUS_CONFIG.created;

  if (loading) {
    return <div className="text-white text-xl">Cargando pedidos...</div>;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-white flex items-center gap-3">
          <ShoppingCart className="text-green-400" />
          Pedidos
        </h1>
        <p className="text-gray-400 mt-1">100k+ pedidos del e-commerce brasileno</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
        <button
          onClick={() => setFiltro(null)}
          className={`p-4 rounded-lg transition-colors ${
            filtro === null ? 'bg-green-600 text-white' : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
          }`}
        >
          <p className="text-2xl font-bold">{orderStats.reduce((a, b) => a + b.count, 0).toLocaleString()}</p>
          <p className="text-sm">Todos</p>
        </button>
        {orderStats.map((stat) => {
          const config = getStatusConfig(stat.status);
          return (
            <button
              key={stat.status}
              onClick={() => setFiltro(stat.status)}
              className={`p-4 rounded-lg transition-colors ${
                filtro === stat.status ? `${config.color} text-white` : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
              }`}
            >
              <p className="text-2xl font-bold">{stat.count.toLocaleString()}</p>
              <p className="text-sm truncate">{config.label}</p>
            </button>
          );
        })}
      </div>

      {/* Lista */}
      <div className="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-700/50">
            <tr className="text-left text-gray-300">
              <th className="px-6 py-4">ID</th>
              <th className="px-6 py-4">Cliente</th>
              <th className="px-6 py-4">Estado</th>
              <th className="px-6 py-4">Fecha</th>
              <th className="px-6 py-4">Items</th>
            </tr>
          </thead>
          <tbody>
            {orders.map((order) => {
              const config = getStatusConfig(order.order_status);
              const Icon = config.icon;
              return (
                <tr key={order.order_id} className="border-t border-gray-700 hover:bg-gray-700/30">
                  <td className="px-6 py-4 text-gray-400 font-mono text-sm">
                    {order.order_id.substring(0, 8)}...
                  </td>
                  <td className="px-6 py-4">
                    <p className="text-white">{order.customer?.customer_city || '-'}</p>
                    <p className="text-gray-500 text-sm">{order.customer?.customer_state}</p>
                  </td>
                  <td className="px-6 py-4">
                    <span className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-sm ${config.color} text-white`}>
                      <Icon size={14} />
                      {config.label}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-gray-300">
                    {order.order_purchase_timestamp
                      ? new Date(order.order_purchase_timestamp).toLocaleDateString('es-ES')
                      : '-'}
                  </td>
                  <td className="px-6 py-4 text-gray-300">
                    {order.items?.length || 0} items
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {orders.length === 0 && (
        <div className="text-center text-gray-500 py-8">
          No hay pedidos con este filtro
        </div>
      )}
    </div>
  );
}

export default Orders;
