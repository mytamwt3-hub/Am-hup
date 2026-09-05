# 📚 دليل مكونات واجهة المستخدم - MetaHub Platform

## نظرة عامة
هذا الدليل يوثق جميع مكونات واجهة المستخدم والأنماط البصرية المستخدمة في منصة MetaHub المُعاد تصميمها بأسلوب **Neon Design**.

---

## 🎨 نظام التصميم (Design System)

### نظام الألوان (Color Palette)

```
الألوان الأساسية:
├── Neon Cyan: #00d4ff / #00ffff
│   └── الاستخدام: العناوين الرئيسية، الحدود المضيئة
├── Neon Purple: #aa00ff
│   └── الاستخدام: التركيزات الثانوية، العناصر المهمة
├── Neon Orange: #ff9900
│   └── الاستخدام: التنبيهات، العمليات الحرجة
├── Neon Red: #ff4444 / #ff6666
│   └── الاستخدام: الأخطاء، المراقبة الأمنية
├── Success Green: #00ff00
│   └── الاستخدام: رسائل النجاح، الحالات الإيجابية
└── Background Dark: #0a0e27, #070617
    └── الاستخدام: الخلفيات الرئيسية، الطبقات
```

### الخطوط المستخدمة
- **الخط الرئيسي**: Segoe UI, Tahoma, Geneva, Verdana, sans-serif
- **الخط الأحادي**: Courier New (للأرقام والأسعار)

### التدرجات والظلال
```css
/* التدرج الأساسي للخلفية */
background: radial-gradient(800px 400px at 10% 10%, rgba(0,212,255,0.04), transparent 6%),
            radial-gradient(600px 300px at 90% 85%, rgba(170,0,255,0.03), transparent 6%),
            linear-gradient(135deg,#070617 0%, #0f1230 100%);

/* توهج Neon */
text-shadow: 0 0 10px #00d4ff, 0 0 24px #0099ff;
box-shadow: 0 0 20px rgba(0, 212, 255, 0.3);
```

---

## 🧩 المكونات الرئيسية

### 1. Header (شريط العنوان)

**الموقع**: جميع الصفحات
**الغرض**: الهوية البصرية والملاحة الأساسية

**الخصائص**:
- خلفية شفافة مع حد سفلي مضيء
- عنوان رئيسي بتأثير توهج Neon
- نص فرعي يوضح وظيفة الصفحة
- ثابت (sticky) عند التمرير

**مثال الكود**:
```html
<header>
    <h1>🌐 MetaHOP</h1>
    <p class="header-subtitle">منصة المتاجر والخدمات المتكاملة</p>
</header>
```

**الأنماط الرئيسية**:
```css
header {
    background: rgba(10, 14, 39, 0.95);
    border-bottom: 2px solid #00d4ff;
    position: sticky;
    top: 0;
    z-index: 1000;
}

header h1 {
    animation: neonPulse 2.2s infinite;
    color: #00ffff;
}
```

---

### 2. Metric Cards (بطاقات المقاييس)

**الموقع**: لوحة التحكم (admin.html)
**الغرض**: عرض المؤشرات المالية الرئيسية

**العناصر المكونة**:
```
┌─────────────────────────────┐
│ 💰 إجمالي الأصول (الكناية)   │
├─────────────────────────────┤
│ 0.00 (القيمة - رقمية)       │
├─────────────────────────────┤
│ 📈 السنة الحالية (التغيير)   │
└─────────────────────────────┘
```

**الخصائص**:
- شبكة تكيفية (auto-fit grid)
- بطاقات بحدود مضيئة
- تأثير توهج متحرك
- قيم رقمية بخط أحادي

**مثال الكود**:
```html
<div class="metric-card">
    <div class="metric-label">💰 إجمالي الأصول</div>
    <div class="metric-value" id="totalAssets">0.00</div>
    <div class="metric-change">
        <span>📈 السنة الحالية</span>
    </div>
</div>
```

**الحسابات**:
```javascript
- إجمالي الأصول = رصيد الصندوق + محفظة التاجر + عمولات المنصة
- معدل التغير = (القيمة_الحالية - القيمة_السابقة) / القيمة_السابقة
```

---

### 3. Invoice Section (قسم الفواتير)

**الموقع**: admin.html
**الغرض**: إنشاء وعرض الفواتير الرسمية

#### 3.1 Invoice Form (نموذج الفاتورة)

**الحقول المطلوبة**:
```
├── رقم الفاتورة (Invoice Number)
│   └── التنسيق: INV-YYYY-NNN
├── التاريخ (Invoice Date)
│   └── نوع: date picker
├── اسم العميل (Client Name)
│   └── نوع: text input
└── رقم الهوية (Client ID)
    └── نوع: text input
```

**الأزرار**:
- **إنشاء فاتورة جديدة**: تولد الفاتورة وتملأ الحقول

#### 3.2 Invoice Display (عرض الفاتورة)

**البنية**:
```
┌─ رأس الفاتورة ─────────────────┐
│ 🧾 فاتورة رسمية                 │
│ INV-2026-001                   │
│ 2026-09-03                     │
└────────────────────────────────┘

┌─ بيانات الطرفين ─────────────────┐
│ من: شركة MetaHOP                │
│ إلى: أحمد محمد السعيد            │
└────────────────────────────────┘

┌─ جدول البنود ──────────────────────┐
│ البيان  │ الوحدة │ السعر │ الكمية │ الإجمالي │
├────────┼────────┼──────┼────────┼──────────┤
│ آيفون 15 Pro    ...              │
│ سماعات AirPods  ...              │
│ حقيبة MacBook   ...              │
└─────────────────────────────────────┘

┌─ الإجماليات ──────────────────┐
│ المجموع (قبل الضريبة): 5738.00   │
│ خصم: 0.00                       │
│ الضريبة (15%): 860.70           │
│ الإجمالي النهائي: 6598.70       │
└─────────────────────────────────┘
```

**الحسابات**:
```javascript
المجموع_قبل_الضريبة = Σ(سعر_الوحدة × الكمية)
الضريبة = المجموع_قبل_الضريبة × 0.15
الإجمالي_النهائي = المجموع_قبل_الضريبة - الخصم + الضريبة
```

---

### 4. Features Slider (من��لق المميزات)

**الموقع**: index.html
**الغرض**: عرض مميزات النظام بشكل تفاعلي

**المميزات المعروضة**:
1. **المحاسب الآلي** - محاسبة تلقائية وتقارير دورية
2. **محفظة الاستثمار** - إدارة الأرباح والاستثمارات
3. **المتجر الإلكتروني** - متجر متكامل بصفحات سريعة
4. **الربط مع الواتساب** - إرسال إشعارات وأتمتة
5. **منظومة التوصيل** - تتبع الشحنات في الوقت الحقيقي
6. **النظام المحاسبي** - إدارة الفواتير والميزانية

**عناصر التحكم**:
- **الأزرار**: ← السابق | النقاط | التالي →
- **التشغيل التلقائي**: تبديل الشريحة كل 5 ثواني
- **التحكم الدوي**: انقر على النقطة أو الأزرار

**الكود**:
```javascript
// الانتقال إلى شريحة محددة
function goTo(i) {
    current = (i + slides.length) % slides.length;
    update();
}

// التشغيل التلقائي
let auto = setInterval(nextSlide, 5000);

// الإيقاف عند التمرير فوق الماوس
featuresEl.addEventListener('mouseenter', () => clearInterval(auto));
```

---

### 5. CCTV Security Section (قسم المراقبة الأمنية)

**الموقع**: admin.html
**الغرض**: البحث عن تسجيلات الكاميرات الأمنية

**معايير البحث**:
- رقم الفاتورة
- التاريخ
- نطاق الوقت (6 ساعات)

**بطاقات النتائج**:
```
┌─ بطاقة الفيديو ────────────────┐
│ عنوان الفيديو                  │
│ ────────────────────────────   │
│ الطابع الزمني: 14:32:15       │
│ المدة: 45 ثانية               │
│ الكاميرا: CAM-01              │
│ ────────────────────────────   │
│ [▶ تشغيل الفيديو]              │
└────────────────────────────────┘
```

---

### 6. Annual Lock Section (قسم القفل السنوي)

**الموقع**: admin.html
**الغرض**: عمليات إغلاق نهاية السنة المالية

**حالات النظام**:
```
┌─ الحالات ──────────────────┐
│ ✓ مُقفل للسنة السابقة      │
│ ✗ غير مُقفل للسنة الحالية │
└─────────────────────────────┘
```

**الأزرار**:
- **تنفيذ القفل السنوي**: ⚠️ عملية حرجة (برتقالي)
- **إلغاء العملية**: إلغاء التأكيد (بنفسجي)

**التنبيهات**:
- رسائل التأكيد (modal)
- رسائل الخطأ / النجاح

---

### 7. Form Components (مكونات النماذج)

#### 7.1 Text Input

```html
<div class="form-group">
    <label>اسم الحقل</label>
    <input type="text" placeholder="مثال">
</div>
```

**الأنماط**:
```css
.form-group input {
    background: rgba(0, 212, 255, 0.05);
    border: 2px solid #00d4ff;
    color: #00ffff;
    padding: 12px;
    transition: all 0.3s;
}

.form-group input:focus {
    background: rgba(0, 212, 255, 0.15);
    box-shadow: 0 0 15px rgba(0, 212, 255, 0.4);
}
```

#### 7.2 Select / Dropdown

```html
<select class="form-group">
    <option>الخيار 1</option>
    <option>الخيار 2</option>
</select>
```

#### 7.3 Date Picker

```html
<input type="date" id="invoiceDate">
```

---

### 8. Buttons (الأزرار)

#### 8.1 أزرار عادية

```html
<button class="btn-lock">تنفيذ العملية</button>
```

#### 8.2 أزرار التحكم في المشاهد

```html
<button class="ctrl-btn" id="prevFeature">◀</button>
<button class="ctrl-btn" id="nextFeature">▶</button>
```

**الأنماط الرئيسية**:
```css
/* زر التنفيذ */
.btn-lock-execute {
    background: linear-gradient(135deg, rgba(255, 153, 0, 0.3), rgba(255, 68, 68, 0.2));
    border: 3px solid #ff9900;
    color: #ff9900;
    transition: all 0.3s;
}

.btn-lock-execute:hover {
    box-shadow: 0 0 30px rgba(255, 153, 0, 0.4);
    transform: scale(1.05);
}

/* زر الإلغاء */
.btn-lock-cancel {
    background: rgba(170, 0, 255, 0.2);
    border-color: #aa00ff;
    color: #aa00ff;
}
```

---

### 9. Animations (الحركات)

#### 9.1 Neon Pulse

```css
@keyframes neonPulse {
    0%, 100% { 
        text-shadow: 0 0 10px #00d4ff, 0 0 24px #0099ff; 
    }
    50% { 
        text-shadow: 0 0 18px #00e6ff, 0 0 34px #aa00ff; 
    }
}
```

**الاستخدام**: عناوين مهمة، ألقاب الأقسام

#### 9.2 Box Glow

```css
@keyframes boxGlow {
    0%, 100% { 
        box-shadow: 0 0 20px rgba(0, 212, 255, 0.3), 0 0 40px rgba(0, 153, 255, 0.2); 
    }
    50% { 
        box-shadow: 0 0 30px rgba(0, 212, 255, 0.5), 0 0 60px rgba(138, 43, 226, 0.3); 
    }
}
```

**الاستخدام**: بطاقات البيانات، الأقسام المهمة

#### 9.3 Slide Down

```css
@keyframes slideDown {
    from { transform: translateY(-20px); opacity: 0; }
    to { transform: translateY(0); opacity: 1; }
}
```

**الاستخدام**: ظهور العناصر، الرسائل

#### 9.4 Count Up

```css
@keyframes countUp {
    from { opacity: 0; }
    to { opacity: 1; }
}
```

**الاستخدام**: ظهور الأرقام

---

## 📐 Responsive Design

### نقاط الفصل (Breakpoints)

```css
/* الشاشات الكبيرة */
@media (min-width: 1000px) {
    .slide { padding: 22px; }
    .slide-visual img { height: 200px; }
}

/* الأجهزة اللوحية */
@media (max-width: 1024px) {
    .invoice-info { grid-template-columns: 1fr; }
    .cctv-search-box { grid-template-columns: 1fr; }
}

/* الهواتف المحمولة */
@media (max-width: 768px) {
    header h1 { font-size: 1.8em; }
    .metrics-section { grid-template-columns: 1fr; }
    .slide { flex-direction: column; }
}

/* الشاشات الصغيرة جداً */
@media (max-width: 480px) {
    .container { padding: 0 10px; }
}
```

---

## ⌨️ التفاعلات والديناميكيات

### 1. Hover Effects (تأثيرات التمرير)

```css
.metric-card:hover {
    transform: scale(1.02);
}

.invoice-items tbody tr:hover {
    background: rgba(0, 212, 255, 0.1);
}

.cctv-card:hover {
    border-color: #00ffff;
    box-shadow: 0 0 20px rgba(0, 212, 255, 0.3);
}
```

### 2. Focus States (حالات التركيز)

```css
input:focus, select:focus {
    outline: none;
    background: rgba(0, 212, 255, 0.15);
    box-shadow: 0 0 15px rgba(0, 212, 255, 0.4);
}
```

### 3. Active States (الحالات النشطة)

```css
.dot.active {
    background: linear-gradient(90deg, #6ee7ff, #ff5ef7);
    box-shadow: 0 0 18px rgba(110, 231, 255, 0.14);
}

.status-box.active {
    border-color: #00ff00;
}
```

---

## 🎯 معايير الوصولية (Accessibility)

### ARIA Labels

```html
<button aria-label="الشريحة السابقة">◀</button>
<div role="tablist" aria-label="محدد الشرائح"></div>
<article role="group" aria-label="المحاسب الآلي"></article>
```

### Semantic HTML

```html
<!-- استخدام العناصر الصحيحة -->
<main>            <!-- المحتوى الرئيسي -->
<header>          <!-- الرأس -->
<nav>             <!-- التنقل -->
<article>         <!-- محتوى مستقل -->
<section>         <!-- قسم محتوى -->
<figure>          <!-- صورة مع تسمية -->
```

### اختبار الوصولية

- ✓ اختبار لوحة المفاتيح
- ✓ توافقية قارئ الشاشة
- ✓ تباين الألوان كافِ
- ✓ حجم الخط قابل للتكبير

---

## 📱 التوافقية

### المتصفحات المدعومة

```
✓ Chrome 90+
✓ Firefox 88+
✓ Safari 14+
✓ Edge 90+
```

### اختبار الأجهزة

```
✓ iPhone 12+
✓ iPad 5th generation+
✓ Android 10+
✓ Windows/Mac Desktop
```

---

## 🔧 اقتراحات الصيانة والتحديث

### الملفات ذات الصلة
- `index.html` - الصفحة الرئيسية
- `admin.html` - لوحة التحكم
- `investments.html` - إدارة الاستثمارات
- `employees.html` - إدارة الموظفين

### التحديثات القادمة المقترحة
- [ ] إضافة نمط Dark Mode مكتمل
- [ ] تحسين الأداء بتقليل حجم CSS
- [ ] إضافة تأثيرات انتقالية بين الصفحات
- [ ] دعم اللغات متعددة بشكل ديناميكي
- [ ] إضافة أنماط طباعة (Print Styles)

---

## 📞 الدعم والمساهمة

للإبلاغ عن مشاكل في الواجهة أو اقتراح تحسينات، يرجى فتح issue في المستودع.

