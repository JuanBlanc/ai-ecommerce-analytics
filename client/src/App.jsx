import { BrowserRouter, Routes, Route, Link, useLocation } from 'react-router-dom';
import { MessageSquare, BarChart3, Package, Users, ShoppingCart, LayoutDashboard, Store, Star } from 'lucide-react';
import Dashboard from './pages/Dashboard';
import Chat from './pages/Chat';
import Orders from './pages/Orders';
import Customers from './pages/Customers';
import Products from './pages/Products';
import Sellers from './pages/Sellers';
import Reviews from './pages/Reviews';

function NavLink({ to, icon: Icon, children }) {
  const location = useLocation();
  const isActive = location.pathname === to;

  return (
    <Link
      to={to}
      className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
        isActive
          ? 'bg-green-600 text-white'
          : 'text-gray-300 hover:bg-gray-700'
      }`}
    >
      <Icon size={20} />
      <span>{children}</span>
    </Link>
  );
}

function Sidebar() {
  return (
    <aside className="w-64 bg-gray-800 min-h-screen p-4">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">Olist</h1>
        <p className="text-gray-400 text-sm">E-Commerce Brasil - 100k+ pedidos</p>
      </div>

      <nav className="space-y-2">
        <NavLink to="/" icon={LayoutDashboard}>Dashboard</NavLink>
        <NavLink to="/chat" icon={MessageSquare}>Chatbot IA</NavLink>
        <NavLink to="/orders" icon={ShoppingCart}>Pedidos</NavLink>
        <NavLink to="/customers" icon={Users}>Clientes</NavLink>
        <NavLink to="/products" icon={Package}>Productos</NavLink>
        <NavLink to="/sellers" icon={Store}>Vendedores</NavLink>
        <NavLink to="/reviews" icon={Star}>Reviews</NavLink>
      </nav>

      <div className="mt-8 p-4 bg-gray-700/50 rounded-lg">
        <p className="text-gray-400 text-xs">Dataset</p>
        <p className="text-white text-sm font-medium">Brazilian E-Commerce</p>
        <p className="text-gray-400 text-xs mt-1">by Olist (Kaggle)</p>
      </div>
    </aside>
  );
}

function App() {
  return (
    <BrowserRouter>
      <div className="flex min-h-screen bg-gray-900">
        <Sidebar />
        <main className="flex-1 p-8 overflow-auto">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/chat" element={<Chat />} />
            <Route path="/orders" element={<Orders />} />
            <Route path="/customers" element={<Customers />} />
            <Route path="/products" element={<Products />} />
            <Route path="/sellers" element={<Sellers />} />
            <Route path="/reviews" element={<Reviews />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;
