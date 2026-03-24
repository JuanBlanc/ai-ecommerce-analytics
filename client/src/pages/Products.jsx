import { useState, useEffect } from 'react';
import { Package, TrendingUp } from 'lucide-react';
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, BarChart, Bar, XAxis, YAxis } from 'recharts';
import { obtenerProducts, obtenerProductosPorCategoria, obtenerTopSelling, obtenerCategorias } from '../api';

const COLORS = ['#10B981', '#3B82F6', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899', '#06B6D4', '#84CC16'];

function Products() {
  const [products, setProducts] = useState([]);
  const [categorias, setCategorias] = useState([]);
  const [topSelling, setTopSelling] = useState([]);
  const [productosPorCategoria, setProductosPorCategoria] = useState([]);
  const [loading, setLoading] = useState(true);
  const [vista, setVista] = useState('categorias');

  useEffect(() => {
    const cargarDatos = async () => {
      try {
        const [productsData, categoriasData, topData, porCategoriaData] = await Promise.all([
          obtenerProducts(30),
          obtenerCategorias(),
          obtenerTopSelling(10),
          obtenerProductosPorCategoria()
        ]);
        setProducts(productsData);
        setCategorias(categoriasData);
        setTopSelling(topData);
        setProductosPorCategoria(porCategoriaData.slice(0, 10));
      } catch (error) {
        console.error('Error cargando products:', error);
      } finally {
        setLoading(false);
      }
    };
    cargarDatos();
  }, []);

  if (loading) {
    return <div className="text-white text-xl">Cargando productos...</div>;
  }

  const formatCurrency = (value) => `R$ ${value.toLocaleString()}`;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-white flex items-center gap-3">
            <Package className="text-purple-400" />
            Productos
          </h1>
          <p className="text-gray-400 mt-1">~33,000 productos en {categorias.length} categorias</p>
        </div>

        <div className="flex gap-2">
          <button
            onClick={() => setVista('categorias')}
            className={`px-4 py-2 rounded-lg transition-colors ${
              vista === 'categorias' ? 'bg-purple-600 text-white' : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
            }`}
          >
            Categorias
          </button>
          <button
            onClick={() => setVista('top')}
            className={`px-4 py-2 rounded-lg transition-colors flex items-center gap-2 ${
              vista === 'top' ? 'bg-green-600 text-white' : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
            }`}
          >
            <TrendingUp size={16} />
            Mas Vendidos
          </button>
        </div>
      </div>

      {vista === 'categorias' ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Distribucion por categoria */}
          <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
            <h2 className="text-xl font-semibold text-white mb-4">Distribucion por Categoria</h2>
            <ResponsiveContainer width="100%" height={350}>
              <PieChart>
                <Pie
                  data={productosPorCategoria}
                  cx="50%"
                  cy="50%"
                  outerRadius={120}
                  dataKey="count"
                  nameKey="category"
                  label={({ category, count }) => `${count}`}
                >
                  {productosPorCategoria.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{ backgroundColor: '#1F2937', border: '1px solid #374151' }}
                  formatter={(value, name, props) => [value.toLocaleString(), props.payload.category]}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>

          {/* Lista categorias */}
          <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
            <h2 className="text-xl font-semibold text-white mb-4">Top Categorias</h2>
            <div className="space-y-3">
              {productosPorCategoria.map((cat, index) => (
                <div key={index} className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div
                      className="w-3 h-3 rounded-full"
                      style={{ backgroundColor: COLORS[index % COLORS.length] }}
                    />
                    <span className="text-white text-sm truncate max-w-[250px]">
                      {cat.category || 'Sin categoria'}
                    </span>
                  </div>
                  <span className="text-purple-400 font-medium">{cat.count.toLocaleString()}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      ) : (
        <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
          <h2 className="text-xl font-semibold text-white mb-4">Categorias Mas Vendidas</h2>
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={topSelling} layout="vertical">
              <XAxis type="number" stroke="#9CA3AF" tickFormatter={(v) => `${(v/1000).toFixed(0)}k`} />
              <YAxis type="category" dataKey="category" stroke="#9CA3AF" width={180} tick={{ fontSize: 11 }} />
              <Tooltip
                contentStyle={{ backgroundColor: '#1F2937', border: '1px solid #374151' }}
                formatter={(value, name) => [
                  name === 'total_revenue' ? formatCurrency(value) : value.toLocaleString(),
                  name === 'total_revenue' ? 'Ingresos' : 'Vendidos'
                ]}
              />
              <Bar dataKey="times_sold" fill="#10B981" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>

          <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-4">
            {topSelling.map((item, index) => (
              <div key={index} className="bg-gray-700/50 rounded-lg p-4 flex justify-between items-center">
                <div>
                  <p className="text-white font-medium truncate max-w-[200px]">{item.category || 'N/A'}</p>
                  <p className="text-gray-400 text-sm">{item.times_sold.toLocaleString()} vendidos</p>
                </div>
                <p className="text-green-400 font-bold">{formatCurrency(item.total_revenue)}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default Products;
