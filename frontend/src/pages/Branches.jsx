import { useEffect, useState } from 'react'
import { useAuthStore } from '../store/authStore'
import { useBranchStore } from '../store/branchStore'
import { Plus, Edit2, Trash2, MapPin, Phone, Mail } from 'lucide-react'

export default function Branches() {
  const { token, tenantId } = useAuthStore()
  const { branches, fetchBranches, createBranch, loading } = useBranchStore()
  const [showForm, setShowForm] = useState(false)
  const [formData, setFormData] = useState({
    name: '',
    code: '',
    city: '',
    country: '',
    phone: '',
    email: '',
    manager_name: ''
  })

  useEffect(() => {
    if (token && tenantId) {
      fetchBranches(token, tenantId)
    }
  }, [token, tenantId])

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (await createBranch(token, tenantId, formData)) {
      setFormData({ name: '', code: '', city: '', country: '', phone: '', email: '', manager_name: '' })
      setShowForm(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-4xl font-bold">الفروع</h1>
          <p className="text-slate-400 mt-1">إدارة جميع فروعك</p>
        </div>
        <button
          onClick={() => setShowForm(!showForm)}
          className="gradient-primary text-white px-6 py-2 rounded-lg hover:shadow-lg-blue transition-all flex items-center gap-2"
        >
          <Plus size={20} /> إضافة فرع جديد
        </button>
      </div>

      {showForm && (
        <div className="glass rounded-xl p-6 border border-slate-700">
          <form onSubmit={handleSubmit} className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <input type="text" placeholder="اسم الفرع" value={formData.name} onChange={(e) => setFormData({...formData, name: e.target.value})} className="bg-slate-800 border border-slate-700 rounded-lg p-3 focus:outline-none focus:border-blue-500" required />
            <input type="text" placeholder="رمز الفرع" value={formData.code} onChange={(e) => setFormData({...formData, code: e.target.value})} className="bg-slate-800 border border-slate-700 rounded-lg p-3 focus:outline-none focus:border-blue-500" required />
            <input type="text" placeholder="المدينة" value={formData.city} onChange={(e) => setFormData({...formData, city: e.target.value})} className="bg-slate-800 border border-slate-700 rounded-lg p-3 focus:outline-none focus:border-blue-500" />
            <input type="text" placeholder="الدولة" value={formData.country} onChange={(e) => setFormData({...formData, country: e.target.value})} className="bg-slate-800 border border-slate-700 rounded-lg p-3 focus:outline-none focus:border-blue-500" />
            <input type="tel" placeholder="الهاتف" value={formData.phone} onChange={(e) => setFormData({...formData, phone: e.target.value})} className="bg-slate-800 border border-slate-700 rounded-lg p-3 focus:outline-none focus:border-blue-500" />
            <input type="email" placeholder="البريد الإلكتروني" value={formData.email} onChange={(e) => setFormData({...formData, email: e.target.value})} className="bg-slate-800 border border-slate-700 rounded-lg p-3 focus:outline-none focus:border-blue-500" />
            <input type="text" placeholder="مدير الفرع" value={formData.manager_name} onChange={(e) => setFormData({...formData, manager_name: e.target.value})} className="bg-slate-800 border border-slate-700 rounded-lg p-3 focus:outline-none focus:border-blue-500" />
            <button type="submit" disabled={loading} className="gradient-primary text-white font-bold px-6 py-3 rounded-lg hover:shadow-lg-blue transition-all disabled:opacity-50">
              {loading ? 'جاري الإضافة...' : 'إضافة'}
            </button>
          </form>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {branches.map(branch => (
          <div key={branch.id} className="glass rounded-xl p-6 border border-slate-700 hover:border-blue-500 transition-all">
            <div className="flex justify-between items-start mb-4">
              <h3 className="text-xl font-bold">{branch.name}</h3>
              <div className="flex gap-2">
                <button className="p-2 hover:bg-slate-700 rounded-lg transition-all"><Edit2 size={18} /></button>
                <button className="p-2 hover:bg-red-900/20 rounded-lg text-red-400 transition-all"><Trash2 size={18} /></button>
              </div>
            </div>
            <p className="text-slate-400 text-sm mb-3">الكود: {branch.code}</p>
            <div className="space-y-2 text-sm">
              {branch.city && <p className="flex items-center gap-2"><MapPin size={16} /> {branch.city}</p>}
              {branch.phone && <p className="flex items-center gap-2"><Phone size={16} /> {branch.phone}</p>}
              {branch.email && <p className="flex items-center gap-2"><Mail size={16} /> {branch.email}</p>}
              {branch.manager_name && <p>مدير: {branch.manager_name}</p>}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
