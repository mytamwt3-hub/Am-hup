# 📁 شجرة ملفات منصة MetaHub Platform (النهائية المحدثة)

## البنية الشاملة للمشروع

```
Am-hup/
│
├── 📄 README.md
│   └── الملف الرئيسي يحتوي على وصف المشروع والمميزات الأساسية
│
├── 📂 docs/
│   ├── UI_COMPONENTS_GUIDE.md
│   │   └── دليل شامل لمكونات الواجهة والتصاميم
│   │       ├─ نظام الألوان (Neon Design)
│   │       ├─ المكونات الرئيسية
│   │       ├─ الحركات والتأثيرات
│   │       ├─ Responsive Design
│   │       ├─ التفاعلات والديناميكيات
│   │       └─ معايير الوصولية
│   │
│   ├── SYSTEM_ARCHITECTURE.md
│   │   └── دليل معماري شامل للنظام
│   │       ├─ البنية المعمارية (Architecture)
│   │       ├─ الأنظمة الفرعية (Subsystems)
│   │       ├─ تدفق البيانات (Data Flow)
│   │       ├─ هيكل قاعدة البيانات (Database Schema)
│   │       ├─ معايير الأمان
│   │       ├─ مؤشرات الأداء (KPIs)
│   │       ├─ نظام الاختبار
│   │       ├─ خطة النشر
│   │       └─ رؤية المستقبل
│   │
│   └── SETUP_AND_INSTALLATION.md
│       └── دليل التثبيت والتشغيل
│           ├─ متطلبات النظام
│           ├─ تثبيت المتطلبات
│           ├─ تشغيل السيرفر الرئيسي
│           ├─ فتح الواجهات
│           ├─ تشغيل الاختبارات
│           ├─ استكشاف الأخطاء
│           ├─ بيانات الدخول التجريبية
│           └─ الدعم والمساعدة
│
├── 📂 data/
│   ├── metahub.db
│   │   └── قاعدة البيانات الرئيسية (SQLite)
│   │       ├─ جدول الحسابات (accounts)
│   │       ├─ جدول القيود (journal_entries)
│   │       ├─ جدول الاستثمارات (investments)
│   │       ├─ جدول الطلبات (orders)
│   │       ├─ جدول الفواتير (invoices)
│   │       ├─ جدول الموظفين (employees)
│   │       └─ جدول الحضور (attendance)
│   │
│   └── metahub.backup-YYYYMMDD.db
│       └── نسخ احتياطية يومية من قاعدة البيانات
│
├── 📂 tests/
│   ├── test_accounting.py
│   │   └── اختبارات وحدة المحاسبة
│   │       ├─ test_create_account
│   │       ├─ test_journal_entry
│   │       ├─ test_balance_calculation
│   │       ├─ test_tax_calculation
│   │       └─ test_account_closure
│   │
│   ├── test_meta_hub.py
│   │   └── اختبارات التكامل الشاملة
│   │       ├─ test_sales_flow
│   │       ├─ test_investment_flow
│   │       ├─ test_invoice_generation
│   │       ├─ test_profit_allocation
│   │       └─ test_year_end_closure
│   │
│   └── __init__.py
│       └── ملف يحول المجلد إلى حزمة Python
│
├── 🐍 Python Backend Files
│   │
│   ├── backend_server.py
│   │   └── خادم الويب الرئيسي (Flask)
│   │       ├─ @app.route('/', methods=['GET'])
│   │       │   └─ تقديم الصفحة الرئيسية
│   │       │
│   │       ├─ @app.route('/api/invoices', methods=['POST'])
│   │       │   └─ API إنشاء الفواتير
│   │       │
│   │       ├─ @app.route('/api/investments', methods=['POST'])
│   │       │   └─ API إنشاء الاستثمارات
│   │       │
│   │       ├─ @app.route('/api/sales', methods=['POST'])
│   │       │   └─ API معالجة المبيعات
│   │       │
│   │       ├─ @app.route('/api/employees', methods=['GET', 'POST'])
│   │       │   └─ API إدارة الموظفين
│   │       │
│   │       └─ if __name__ == '__main__':
│   │           └─ app.run(debug=True, port=5000)
│   │
│   ├── accounting_core.py
│   │   └── نواة النظام المحاسبي
│   │       ├─ class Account
│   │       │   ├─ account_id
│   │       │   ├─ account_name
│   │       │   ├─ account_type (asset, liability, etc.)
│   │       │   └─ current_balance
│   │       │
│   │       ├─ class Transaction
│   │       │   ├─ description
│   │       │   ├─ entries[] (debit/credit)
│   │       ���   └─ commit()
│   │       │
│   │       ├─ def buyFromStore()
│   │       │   └─ معالجة عملية الشراء
│   │       │
│   │       ├─ def allocate_sale_for_order()
│   │       │   └─ تخصيص البيع للاستثمارات
│   │       │
│   │       └─ def generate_financial_report()
│   │           └─ توليد التقارير المالية
│   │
│   ├── chart_of_accounts.py
│   │   └── دليل الحسابات (الفئات المحاسبية)
│   │       ├─ 111: حساب الصندوق (Cash Box)
│   │       ├─ 116: محفظة التاجر (Merchant Wallet)
│   │       ├─ 200: الذمم المدينة (Accounts Receivable)
│   │       ├─ 300: الذمم الدائنة (Accounts Payable)
│   │       ├─ 400: الإيرادات (Income)
│   │       ├─ 410: المبيعات (Sales)
│   │       ├─ 417: عمولات المنصة (Platform Commissions)
│   │       ├─ 500: المصروفات (Expenses)
│   │       └─ ... (حسابات أخرى)
│   │
│   ├── investments.py
│   │   └── محرك إدارة الاستثمارات
│   │       ├─ class Investment
│   │       │   ├─ investment_id
│   │       │   ├─ user_id
│   │       │   ├─ product_code
│   │       │   ├─ initial_quantity
│   │       │   ├─ remaining_quantity
│   │       │   └─ profit_realized
│   │       │
│   │       ├─ def create_investment()
│   │       │   └─ إنشاء محفظة جديدة
│   │       │
│   │       ├─ def allocate_sale_for_order()
│   │       │   └─ توزيع المبيعات على الاستثمارات
│   │       │
│   │       ├─ def calculate_roi()
│   │       │   └─ حساب معدل العائد
│   │       │
│   │       └─ def close_investment()
│   │           └─ إغلاق الاستثمار المكتمل
│   │
│   └── requirements.txt
│       └── قائمة المكتبات المطلوبة
│           ├─ Flask==2.3.0
│           ├─ sqlite3
│           ├─ requests==2.31.0
│           ├─ python-dotenv==1.0.0
│           └─ pytest==7.4.0
│
├── 🌐 HTML Frontend Pages
│   │
│   ├── index.html
│   │   └── الصفحة الرئيسية - شاشة الترحيب
│   │       ├─ <header> - الرأس بـ Neon Design
│   │       ├─ <main class="container">
│   │       │   ├─ Features Slider (6 شرائح)
│   │       │   │   ├─ المحاسب الآلي
│   │       │   │   ├─ محفظة الاستثمار
│   │       │   │   ├─ المتجر الإلكتروني
│   │       │   │   ├─ الربط مع الواتساب
│   │       │   │   ├─ منظومة التوصيل
│   │       │   │   └─ النظام المحاسبي المتكامل
│   │       │   │
│   │       │   ├─ <section class="features">
│   │       │   │   ├─ Brand Logo (MH)
│   │       │   │   ├─ Slide Viewport
│   │       │   │   ├─ Navigation Controls
│   │       │   │   └─ Progress Dots
│   │       │   │
│   │       │   └─ Original Store Sections
│   │       │
│   │       ├─ <style> - تنسيقات Neon مكتملة
│   │       │   ├─ Body Gradient
│   │       │   ├─ Header Animations
│   │       │   ├─ Slider CSS
│   │       │   ├─ Controls Styling
│   │       │   └─ Responsive Breakpoints
│   │       │
│   │       └─ <script> - منطق الشريط المتحرك
│   │           ├�� Slider Controller
│   │           ├─ Navigation Logic
│   │           ├─ Auto-play (5 seconds)
│   │           └─ Keyboard Support
│   │
│   ├── admin.html
│   │   └── لوحة التحكم المحاسبية (Admin Dashboard)
│   │       ├─ <header>
│   │       │   ├─ 🔐 عنوان اللوحة
│   │       │   ├─ معلومات مدير النظام
│   │       │   └─ ساعة ديجيتال حية
│   │       │
│   │       ├─ <section class="metrics-section">
│   │       │   ├─ 💰 Metric Card - إجمالي الأصول
│   │       │   ├─ 🏦 Metric Card - رصيد الصندوق
│   │       │   ├─ 📊 Metric Card - محفظة التاجر
│   │       │   └─ 🔌 Metric Card - عمولات المنصة
│   │       │
│   │       ├─ <section class="section">
│   │       │   ├─ Invoice Controls (Form)
│   │       │   │   ├─ رقم الفاتورة (INV-YYYY-NNN)
│   │       │   │   ├─ التاريخ (Date Picker)
│   │       │   │   ├─ اسم العميل
│   │       │   │   └─ رقم الهوية
│   │       │   │
│   │       │   ├─ <div class="invoice-container">
│   │       │   │   ├─ Invoice Header
│   │       │   │   ├─ Company & Customer Info
│   │       │   │   ├─ Items Table
│   │       │   │   └─ Totals Calculation
│   │       │   │
│   │       │   └─ Styling
│   │       │       ├─ Neon Borders
│   │       │       ├─ Animations
│   │       │       └─ Responsive Grid
│   │       │
│   │       ├─ <section class="cctv-section">
│   │       │   ├─ CCTV Search Box
│   │       │   │   ├─ Search by Invoice Number
│   │       │   │   ├─ Search by Date
│   │       │   │   ├─ Time Range Selector
│   │       │   │   └─ Search Button
│   │       │   │
│   │       │   └─ CCTV Results Grid
│   │       │       ├─ Video Card 1
│   │       │       ├─ Video Card 2
│   │       │       └─ Play Buttons
│   │       │
│   │       ├─ <section class="lock-section">
│   │       │   ├─ Annual Year-End Lock
│   │       │   ├─ Status Display
│   │       │   ├─ Execute Lock Button
│   │       │   ├─ Cancel Button
│   │       │   └─ Confirmation Modal
│   │       │
│   │       ├─ <style> - Neon Admin Theme
│   │       │   ├─ Dark Gradient Background
│   │       │   ├─ Neon Cyan Borders
│   │       │   ├─ Neon Purple Accents
│   │       │   ├─ Glowing Effects
│   │       │   ├─ Animations (neonPulse, boxGlow)
│   │       │   ├─ Modal Styling
│   │       │   └─ Responsive Adjustments
│   │       │
│   │       └─ <script> - Admin Interactivity
│   │           ├─ generateInvoice()
│   │           ├─ searchCCTV()
│   │           ├─ lockYearEnd()
│   │           ├─ Modal Controllers
│   │           └─ Real-time Clock
│   │
│   ├── investments.html
│   │   └── واجهة إدارة الاستثمارات
│   │       ├─ New Investment Form
│   │       ├─ Active Portfolio Display
│   │       ├─ Performance Metrics
│   │       ├─ Profit Distribution Panel
│   │       ├─ Investment History Table
│   │       └─ ROI Charts & Graphs
│   │
│   ├── employees.html
│   │   └── واجهة إدارة الموظفين
│   │       ├─ Employee Management Form
│   │       ├─ Employee List Table
│   │       ├─ Attendance & Absence Tracking
│   │       ├─ Salary Calculation Module
│   │       ├─ Monthly Reports
│   │       └─ Payslip Generation
│   │
│   ├── login.html
│   │   └── صفحة تسجيل الدخول
│   │       ├─ Login Form
│   │       │   ├─ Email/Username Input
│   │       │   ├─ Password Input
│   │       │   ├─ Remember Me Checkbox
│   │       │   └─ Login Button
│   │       │
│   │       ├─ Forgot Password Link
│   │       ├─ Registration Link
│   │       ├─ Social Login Options (Future)
│   │       └─ Neon Styled Form
│   │
│   ├── register_personal.html
│   │   └── نموذج التسجيل الشخصي
│   │       ├─ Personal Information
│   │       ├─ Contact Details
│   │       ├─ Account Credentials
│   │       └─ Terms & Conditions
│   │
│   ├── register_business.html
│   │   └── نموذج التسجيل التجاري
│   │       ├─ Business Information
│   │       ├─ Commercial Registration
│   │       ├─ Business Type Selection
│   │       └─ Terms & Conditions
│   │
│   ├── welcome.html
│   │   └── صفحة الترحيب والإرشادات
│   │       ├─ Welcome Message
│   │       ├─ Getting Started Guide
│   │       ├─ Feature Overview
│   │       └─ CTA (Call to Action)
│   │
│   ├── privacy_policy.html
│   │   └── سياسة الخصوصية
│   │       ├─ Data Protection Policy
│   │       ├─ Cookie Policy
│   │       ├─ Third-party Services
│   │       └─ Contact Information
│   │
│   └── terms_of_service.html
│       └── شروط الخدمة
│           ├─ User Rights & Responsibilities
│           ├─ Service Terms
│           ├─ Limitation of Liability
│           ├─ Dispute Resolution
│           └─ Changes to Terms
│
├── 📋 Configuration Files
│   │
│   ├── .env
│   │   └── متغيرات البيئة (لا تُرفع على GitHub)
│   │       ├─ FLASK_ENV=development
│   │       ├─ FLASK_DEBUG=True
│   │       ├─ DATABASE_URL=sqlite:///metahub.db
│   │       ├─ SECRET_KEY=your-secret-key
│   │       └─ API_KEY=your-api-key
│   │
│   ├── .gitignore
│   │   └��─ ملفات يتم تجاهلها
│   │       ├─ *.db
│   │       ├─ __pycache__/
│   │       ├─ .env
│   │       ├─ .pytest_cache/
│   │       └─ venv/
│   │
│   ├── requirements.txt
│   │   └── مكتبات Python
│   │
│   └── config.py
│       └── إعدادات التطبيق
│           ├─ DATABASE_CONFIG
│           ├─ SECURITY_SETTINGS
│           └─ API_CONFIGURATION
│
├── 📊 Analytics & Monitoring
│   │
│   └── logs/
│       ├─ app.log
│       ├─ error.log
│       ├─ access.log
│       └─ audit.log
│
└── 📦 Additional Resources
    │
    ├── .github/
    │   └── workflows/
    │       ├─ ci.yml (Continuous Integration)
    │       └─ deploy.yml (Deployment Pipeline)
    │
    ├── docker/
    │   ├─ Dockerfile
    │   └─ docker-compose.yml
    │
    └── scripts/
        ├─ setup.sh (Setup Script)
        ├─ backup.sh (Backup Script)
        ├─ deploy.sh (Deployment Script)
        └─ migrate.sh (Database Migration Script)
```

---

## 📊 إحصائيات المشروع

```
عدد الملفات الرئيسية: 19
├─ Python Files: 5
├─ HTML Files: 11
├─ Test Files: 2
├─ Configuration Files: 1

عدد أسطر الكود: ~15,000+
├─ Frontend (HTML/CSS/JS): ~8,000
├─ Backend (Python): ~5,000
├─ Tests: ~2,000

حجم المستودع: 216 KB
الإصدار الحالي: 1.0
الحالة: جاهز للإنتاج ✅
```

---

## 🔄 تدفق الملفات والاتصالات

```
المستخدم
    ↓
[متصفح الويب]
    ↓
┌─────────────────────────────────┐
│      Requests to Endpoints      │
└─────────────────────────────────┘
    ↓
[backend_server.py - Flask]
    ├─ GET /          → index.html
    ├─ GET /admin     → admin.html
    ├─ POST /api/*    → Processes Business Logic
    └─ Static Files   → HTML/CSS/JS
    ↓
┌─────────────────────────────────┐
│  Backend Logic Processing       │
└─────────────────────────────────┘
    ↓
├─ [accounting_core.py]  ← معالجة محاسبية
├─ [investments.py]       ← منطق الاستثمارات
└─ [chart_of_accounts.py]← دليل الحسابات
    ↓
┌─────────────────────────────────┐
│   Database Operations           │
└─────────────────────────────────┘
    ↓
[metahub.db - SQLite]
    ├─ accounts table
    ├─ transactions table
    ├─ investments table
    ├─ orders table
    ├─ invoices table
    ├─ employees table
    └─ attendance table
    ↓
[Response with Data]
    ↓
[HTML Page Rendered]
    ↓
[User Interface Updated]
```

---

## 🎯 ملفات الأهمية العالية

### يجب عدم حذفها أو تعديلها بدون احتياط:

```
🔴 CRITICAL (حرج):
├─ metahub.db (قاعدة البيانات الرئيسية)
├─ backend_server.py (الخادم الرئيسي)
└─ accounting_core.py (نواة المحاسبة)

🟠 IMPORTANT (مهم):
├─ admin.html (لوحة التحكم)
├─ investments.py (منطق الاستثمارات)
└─ chart_of_accounts.py (دليل الحسابات)

🟡 MODERATE (متوسط):
├─ index.html (الصفحة الرئيسية)
├─ employees.html (إدارة الموظفين)
└─ investments.html (إدارة الاستثمارات)

🟢 OPTIONAL (اختياري):
├─ login.html (تسجيل الدخول)
├─ privacy_policy.html (السياسات)
└─ terms_of_service.html (الشروط)
```

---

## 📈 مسار التطوير المستقبلي

```
المرحلة الحالية (Current): v1.0 - أساسي
    ↓
المرحلة القادمة (Next): v1.1 - تحسينات
    ├─ دعم العملات المتعددة
    ├─ نظام CRM متقدم
    └─ تقارير موسعة
    ↓
المرحلة 2: v2.0 - موبايل
    ├─ تطبيق iOS/Android
    ├─ API RESTful محسّنة
    └─ مزامنة البيانات
    ↓
المرحلة 3: v3.0 - AI & Analytics
    ├─ نبؤات ذكية
    ├─ تحليلات متقدمة
    └─ أتمتة كاملة
```

---

## 🔐 ملاحظات الأمان

```
⚠️ لا تشارك:
├─ .env file
├─ metahub.db (البيانات الفعلية)
├─ SECRET_KEY
└─ API_KEYS

✅ يمكن مشاركتها:
├─ Source code (Python/HTML)
├─ Documentation
├─ Configuration examples
└─ Test files
```

---

**آخر تحديث**: 2026-09-05
**الإصدار**: 1.0
**حالة الملفات**: ✅ كاملة وجاهزة للاستخدام

