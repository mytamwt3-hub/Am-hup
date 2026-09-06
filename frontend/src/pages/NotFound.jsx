import { Link } from 'react-router-dom'

export default function NotFound() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 to-slate-800">
      <div className="text-center">
        <h1 className="text-6xl font-bold mb-4">404</h1>
        <p className="text-xl text-slate-400 mb-8">الصفحة غير موجودة</p>
        <Link to="/" className="gradient-primary text-white px-6 py-3 rounded-lg hover:shadow-lg-blue transition-all inline-block">
          العودة للرئيسية
        </Link>
      </div>
    </div>
  )
}
