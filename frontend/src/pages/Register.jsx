import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import { Mail, Lock, User, Phone, Loader, Building2 } from 'lucide-react'

export default function Register() {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    full_name: '',
    phone: '',
    entity_type: 'company',
    entity_name: ''
  })
  const { register, loading, error } = useAuthStore()
  const navigate = useNavigate()

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value })
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (await register(formData)) {
      navigate('/')
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-4">
      <div className="w-full max-w-md">
        <div className="glass rounded-2xl p-8 shadow-lg-blue">
          <h1 className="text-3xl font-bold text-center mb-2 gradient-primary bg-clip-text text-transparent">Am-hup</h1>
          <p className="text-center text-slate-400 mb-8">إنشاء حساب جديد</p>

          {error && (
            <div className="bg-red-900/20 border border-red-700 text-red-200 px-4 py-3 rounded-lg mb-6">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">نوع الكيان</label>
              <select name="entity_type" value={formData.entity_type} onChange={handleChange} className="w-full bg-slate-800 border border-slate-700 rounded-lg py-2 px-4 focus:outline-none focus:border-blue-500">
                <option value="company">شركة</option>
                <option value="establishment">مؤسسة</option>
                <option value="branch">فرع</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">اسم الكيان</label>
              <div className="relative">
                <Building2 className="absolute right-3 top-3 text-slate-500" size={20} />
                <input
                  type="text"
                  name="entity_name"
                  value={formData.entity_name}
                  onChange={handleChange}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg py-2 pr-10 pl-4 focus:outline-none focus:border-blue-500 transition-all"
                  placeholder="اسم الشركة أو المؤسسة"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">الاسم الكامل</label>
              <div className="relative">
                <User className="absolute right-3 top-3 text-slate-500" size={20} />
                <input
                  type="text"
                  name="full_name"
                  value={formData.full_name}
                  onChange={handleChange}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg py-2 pr-10 pl-4 focus:outline-none focus:border-blue-500 transition-all"
                  placeholder="اسمك الكامل"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">رقم الجوال</label>
              <div className="relative">
                <Phone className="absolute right-3 top-3 text-slate-500" size={20} />
                <input
                  type="tel"
                  name="phone"
                  value={formData.phone}
                  onChange={handleChange}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg py-2 pr-10 pl-4 focus:outline-none focus:border-blue-500 transition-all"
                  placeholder="+966501234567"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">البريد الإلكتروني</label>
              <div className="relative">
                <Mail className="absolute right-3 top-3 text-slate-500" size={20} />
                <input
                  type="email"
                  name="email"
                  value={formData.email}
                  onChange={handleChange}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg py-2 pr-10 pl-4 focus:outline-none focus:border-blue-500 transition-all"
                  placeholder="بريدك الإلكتروني"
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
                  name="password"
                  value={formData.password}
                  onChange={handleChange}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg py-2 pr-10 pl-4 focus:outline-none focus:border-blue-500 transition-all"
                  placeholder="كلمة مرور قوية"
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
              {loading ? 'جاري الإنشاء...' : 'إنشاء حساب'}
            </button>
          </form>

          <p className="text-center text-slate-400 mt-6">
            لديك حساب بالفعل؟ <Link to="/login" className="text-blue-400 hover:text-blue-300">دخول</Link>
          </p>
        </div>
      </div>
    </div>
  )
}
