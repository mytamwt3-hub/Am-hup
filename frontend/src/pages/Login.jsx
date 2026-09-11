import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import { Mail, Lock, Loader } from 'lucide-react'

export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const { login, loading, error } = useAuthStore()
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (await login(email, password)) {
      navigate('/')
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-4">
      <div className="w-full max-w-md">
        <div className="glass rounded-2xl p-8 shadow-lg-blue">
          <h1 className="text-3xl font-bold text-center mb-2 gradient-primary bg-clip-text text-transparent">Am-hup</h1>
          <p className="text-center text-slate-400 mb-8">منصة الأعمال العالمية المتكاملة</p>

          {error && (
            <div className="bg-red-900/20 border border-red-700 text-red-200 px-4 py-3 rounded-lg mb-6">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">البريد الإلكتروني</label>
              <div className="relative">
                <Mail className="absolute right-3 top-3 text-slate-500" size={20} />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg py-2 pr-10 pl-4 focus:outline-none focus:border-blue-500 transition-all"
                  placeholder="أدخل بريدك الإلكتروني"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">كلمة المرور</label>
              <div className="relative">
                <Lock className="absolute right-3 top-3 text-slate-500" size={20} />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg py-2 pr-10 pl-4 focus:outline-none focus:border-blue-500 transition-all"
                  placeholder="أدخل كلمة مرورك"
                  required
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full gradient-primary text-white font-bold py-2 rounded-lg hover:shadow-lg-blue transition-all disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {loading ? <Loader size={20} className="animate-spin" /> : null}
              {loading ? 'جاري الدخول...' : 'دخول'}
            </button>
          </form>

          <p className="text-center text-slate-400 mt-6">
            ليس لديك حساب؟ <Link to="/register" className="text-blue-400 hover:text-blue-300">سجل الآن</Link>
          </p>
        </div>
      </div>
    </div>
  )
}
