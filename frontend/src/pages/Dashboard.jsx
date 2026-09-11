import { useEffect, useState } from 'react'
import { useAuthStore } from '../store/authStore'
import { useBranchStore } from '../store/branchStore'
import { TrendingUp, Users, MapPin, DollarSign } from 'lucide-react'

export default function Dashboard() {
  const { token, tenantId, user } = useAuthStore()
  const { branches, fetchBranches } = useBranchStore()
  const [stats, setStats] = useState(null)

  useEffect(() => {
    if (token && tenantId) {
      fetchBranches(token, tenantId)
    }
  }, [token, tenantId])

  const StatCard = ({ icon: Icon, label, value, color }) => (
    <div className="glass rounded-xl p-6 border border-slate-700">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-slate-400 text-sm">{label}</p>
          <p className="text-3xl font-bold mt-2">{value}</p>
        </div>
        <div className={`p-3 rounded-lg ${color}`}>
          <Icon size={24} />
        </div>
      </div>
    </div>
  )

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-4xl font-bold mb-2">مرحباً بك في لوحة التحكم</h1>
        <p className="text-slate-400">إدارة أعمالك بسهولة وكفاءة</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard icon={MapPin} label="عدد الفروع" value={branches.length} color="gradient-primary" />
        <StatCard icon={Users} label="المستخدمون" value="5" color="gradient-success" />
        <StatCard icon={DollarSign} label="المبيعات" value="15,000 ر.س" color="bg-yellow-900/20" />
        <StatCard icon={TrendingUp} label="النمو" value="+23%" color="bg-green-900/20" />
      </div>

      <div className="glass rounded-xl p-6 border border-slate-700">
        <h2 className="text-2xl font-bold mb-4">الفروع الأخيرة</h2>
        <div className="space-y-2">
          {branches.length > 0 ? (
            branches.slice(0, 5).map(branch => (
              <div key={branch.id} className="flex justify-between items-center p-4 bg-slate-800/50 rounded-lg">
                <div>
                  <p className="font-bold">{branch.name}</p>
                  <p className="text-sm text-slate-400">{branch.city}</p>
                </div>
                <p className="text-green-400">نشط</p>
              </div>
            ))
          ) : (
            <p className="text-slate-400">لا توجد فروع بعد</p>
          )}
        </div>
      </div>
    </div>
  )
}
