import { Outlet, Link, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import { Menu, X, LogOut, Home, MapPin, Users, Settings } from 'lucide-react'
import { useState } from 'react'

export default function Layout() {
  const { logout, user } = useAuthStore()
  const [menuOpen, setMenuOpen] = useState(false)
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-900 to-slate-800">
      {/* Header */}
      <header className="glass sticky top-0 z-50 border-b border-slate-700">
        <div className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold gradient-primary bg-clip-text text-transparent">Am-hup</h1>
          <button onClick={() => setMenuOpen(!menuOpen)} className="md:hidden">
            {menuOpen ? <X size={24} /> : <Menu size={24} />}
          </button>
        </div>
      </header>

      <div className="flex flex-col md:flex-row">
        {/* Sidebar */}
        <aside className={`${menuOpen ? 'block' : 'hidden'} md:block w-full md:w-64 glass border-l border-slate-700 p-4`}>
          <nav className="space-y-2">
            <Link to="/" className="flex items-center gap-3 px-4 py-2 rounded-lg hover:bg-slate-700 transition-all">
              <Home size={20} /> لوحة التحكم
            </Link>
            <Link to="/branches" className="flex items-center gap-3 px-4 py-2 rounded-lg hover:bg-slate-700 transition-all">
              <MapPin size={20} /> الفروع
            </Link>
            <Link to="/users" className="flex items-center gap-3 px-4 py-2 rounded-lg hover:bg-slate-700 transition-all">
              <Users size={20} /> المستخدمون
            </Link>
            <Link to="/settings" className="flex items-center gap-3 px-4 py-2 rounded-lg hover:bg-slate-700 transition-all">
              <Settings size={20} /> الإعدادات
            </Link>
            <button onClick={handleLogout} className="w-full flex items-center gap-3 px-4 py-2 rounded-lg hover:bg-red-900/20 text-red-400 transition-all">
              <LogOut size={20} /> تسجيل الخروج
            </button>
          </nav>
        </aside>

        {/* Main Content */}
        <main className="flex-1 p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
