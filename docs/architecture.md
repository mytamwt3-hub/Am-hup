---
layout: default
title: "MetaHOP Architecture — الأنظمة العشرة"
---

<style>
:root{
  --bg:#07102a;
  --card:#0f1730;
  --accent1:#00d4ff;
  --accent2:#aa00ff;
  --glass: rgba(255,255,255,0.03);
}
body{background: linear-gradient(135deg,#07102a 0%, #0b1230 50%, #081026 100%);color:#e6f0ff;font-family: Inter, system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial;line-height:1.45;padding:40px}
.container{max-width:1120px;margin:0 auto}
.header{display:flex;gap:20px;align-items:center;margin-bottom:28px}
.logo{width:120px;height:120px;flex:0 0 120px;border-radius:14px;background:linear-gradient(135deg,var(--accent1),var(--accent2));display:flex;align-items:center;justify-content:center;box-shadow:0 10px 40px rgba(0,212,255,0.08),0 0 60px rgba(170,0,255,0.06);overflow:hidden}
.logo img{width:100%;height:100%;object-fit:cover;filter:drop-shadow(0 6px 18px rgba(0,212,255,0.25))}
.title{flex:1}
.title h1{font-size:28px;margin:0;color:var(--accent1);text-shadow:0 0 18px rgba(0,212,255,0.18)}
.title p{margin:6px 0 0;color:#c8d7ff}
.badge{display:inline-block;background:linear-gradient(90deg,var(--accent1),var(--accent2));padding:6px 12px;border-radius:999px;color:#07102a;font-weight:700;margin-left:10px}

.grid{display:grid;grid-template-columns:repeat(5,1fr);gap:18px;margin-top:30px}
@media (max-width:1100px){.grid{grid-template-columns:repeat(3,1fr)}}
@media (max-width:700px){.grid{grid-template-columns:repeat(1,1fr)}}

.card{background:linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01));border:1px solid rgba(255,255,255,0.04);padding:18px;border-radius:12px;position:relative;overflow:hidden;cursor:pointer;transition:transform .25s ease,box-shadow .25s}
.card:hover{transform:translateY(-6px);box-shadow:0 12px 40px rgba(0,0,0,0.45),0 0 30px rgba(0,212,255,0.06)}
.card .num{position:absolute;right:14px;top:14px;color:rgba(255,255,255,0.08);font-weight:900;font-size:60px}
.card h3{margin:0;color:var(--accent1);font-size:18px}
.card p{color:#c6d6ff;margin:8px 0 0;font-size:14px}
.card .meta{margin-top:12px;display:flex;gap:8px;flex-wrap:wrap}
.meta .chip{background:var(--glass);padding:6px 10px;border-radius:999px;border:1px solid rgba(255,255,255,0.03);font-size:13px;color:#bcd8ff}

/* Glow ribbon */
.card::after{content:'';position:absolute;left:-40%;top:-40%;width:200%;height:200%;background:radial-gradient(circle at 10% 10%, rgba(0,212,255,0.09), transparent 8%), radial-gradient(circle at 90% 90%, rgba(170,0,255,0.06), transparent 12%);pointer-events:none}

/* modal / detail */
.detail-panel{position:fixed;right:20px;left:20px;top:80px;bottom:40px;background:linear-gradient(180deg, rgba(10,14,39,0.98), rgba(10,14,39,0.96));border:1px solid rgba(0,212,255,0.06);border-radius:12px;box-shadow:0 30px 80px rgba(0,0,0,0.6);padding:24px;display:none;flex-direction:column;z-index:2000}
.detail-panel.active{display:flex}
.detail-header{display:flex;align-items:center;gap:16px}
.detail-header h2{margin:0;color:var(--accent2)}
.detail-body{margin-top:18px;color:#cddcff;flex:1;overflow:auto}
.detail-footer{text-align:right;margin-top:12px}
.btn-close{background:transparent;border:1px solid rgba(255,255,255,0.04);color:#cfeaff;padding:8px 12px;border-radius:8px;cursor:pointer}

/* engineering table layout */
.engineering-grid{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin-top:26px}
@media (max-width:900px){.engineering-grid{grid-template-columns:1fr}}
.engineering-left{background:linear-gradient(180deg, rgba(255,255,255,0.02), transparent);padding:18px;border-radius:12px;border:1px solid rgba(255,255,255,0.03)}
.engineering-right{display:flex;align-items:center;justify-content:center}
.hero-image{width:100%;max-width:360px;border-radius:12px;padding:12px;background:linear-gradient(135deg, rgba(0,212,255,0.06), rgba(170,0,255,0.06));box-shadow:0 20px 60px rgba(0,212,255,0.06)}
.hero-image img{width:100%;height:auto;display:block}
.caption{color:#9fc7ff;margin-top:10px}

/* interactive legend */
.legend{display:flex;gap:12px;flex-wrap:wrap;margin-top:14px}
.legend .item{display:flex;gap:8px;align-items:center}
.legend .swatch{width:26px;height:26px;border-radius:6px;background:linear-gradient(135deg,var(--accent1),var(--accent2));box-shadow:0 6px 18px rgba(0,212,255,0.12)}

/* subtle animations */
@keyframes neonPulse{0%{box-shadow:0 0 8px rgba(0,212,255,0.08)}50%{box-shadow:0 0 18px rgba(0,212,255,0.12)}100%{box-shadow:0 0 8px rgba(0,212,255,0.08)}}
.logo{animation:neonPulse 3s infinite}

</style>

<div class="container">
  <header class="header">
    <div class="logo" aria-hidden="true">
      <img src="/assets/accountant-neon.png" alt="محاسب MetaHOP المضيء — ضع صورتك هنا">
    </div>
    <div class="title">
      <h1>MetaHOP — الهندسة المعمارية للنظام (الأنظمة العشرة)</h1>
      <p>عرض تفاعلي موجز للمستثمرين مع مؤثرات نيرانية وصور المحاسب الذكي المضيء</p>
    </div>
    <div class="badge">Investor Deck</div>
  </header>

  <section class="engineering-grid">
    <div class="engineering-left">
      <p style="color:#bfe6ff">أنظمة منصة MetaHOP مصممة لتكون متكاملة، قابلة للتوسع، ومهيأة للتشغيل التجاري الفعلي. اضغط على أي نظام لعرض تفاصيله التقنية، نموذج العمل، ومؤشرات الأداء المقترحة.</p>

      <div class="grid" id="systemsGrid">
        <!-- 10 systems cards generated by JS -->
      </div>

      <div style="margin-top:18px;display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap">
        <div class="legend">
          <div class="item"><span class="swatch"></span><strong>Neon UX</strong></div>
          <div class="item"><span style="width:26px;height:26px;border-radius:6px;background:#0f1630;display:inline-block"></span><strong>Backend Core</strong></div>
        </div>
        <div style="color:#9fb9ff;font-size:13px">حالة: <strong style="color:var(--accent1)">جاهز للتجربة</strong></div>
      </div>
    </div>

    <aside class="engineering-right">
      <div class="hero-image">
        <img src="/assets/accountant-neon.png" alt="المحاسب الذكي المضيء" />
        <div class="caption">صورة المحاسب الذكي المضيء — موضع مخصص للعرض</div>
      </div>
    </aside>
  </section>

  <div class="detail-panel" id="detailPanel">
    <div class="detail-header">
      <h2 id="detailTitle">تفاصيل النظام</h2>
      <div style="flex:1"></div>
      <button class="btn-close" onclick="closeDetail()">إغلاق</button>
    </div>
    <div class="detail-body" id="detailBody"></div>
    <div class="detail-footer"><small style="color:#9ebefc">MetaHOP • Architecture • Investor Preview</small></div>
  </div>
</div>

<script>
const systems = [
  {id:1, title:'نواة الحسابات (Accounting Core)', summary:'دقة Decimal، قيد مزدوج، معاملات متوازنة.', detail:'الوظائف الأساسية: Account, Transaction, Entry. دعم Decimal بدقة عالية، حفظ persistence، وإجراءات إقفال محاسبي آمن.'},
  {id:2, title:'نظام المتجر والمخزون (Store & Inventory)', summary:'منتجات، مخزون، أوامر، ومزامنة مع CCTV.', detail:'يدير PRODUCTS, INVENTORY, ORDERS ويدعم أوضاع تجزئة/جملة ومزامنة فواتير مع لقطات الكاميرا.'},
  {id:3, title:'نظام البصمة والموارد البشرية (HR & Biometric)', summary:'تسجيل حضور، خصومات دقيقة، تنبيهات تراكمية.', detail:'يدعم حساب دقائق التأخير بدقة Decimal، حفظ أوفلاين، وشروط إنذار تراكمية مع سجل تاريخه.'},
  {id:4, title:'نظام الإشعارات والواتساب (Notifications & WhatsApp)', summary:'محاكاة إشعارات أوفلاين، بوابة لتكامل مزود لاحق.', detail:'حفظ إشعارات داخلية في WHATSAPP_NOTIFICATIONS, دعم إرسال فعلي عبر موفر خارجي (ممكن إضافة Twilio/Meta API).'},
  {id:5, title:'نظام الدردشة داخل التطبيق (In-app Chat)', summary:'مراسلات فورية، محفوظات، واسترجاع حسب المستلم.', detail:'سجل CHAT_MESSAGE_LOGS، عمليات إرسال واسترجاع، وواجهات لربط مع UI.'},
  {id:6, title:'نظام الجملة واللوجستيات (Wholesale & Logistics)', summary:'إدارة عبوات، تخفيضات جملة، ومستودعات متعددة.', detail:'دعم صناديق/علب بكميات كبيرة، قواعد تسعير مختلفة، وواجهات لادارة محطات شحن.'},
  {id:7, title:'CCTV Invoice Sync', summary:'مزامنة الفواتير مع لقطات الكاميرا كدليل.', detail:'يسجل CCTV_INVOICE_LOGS ويربط invoice_id مع فيديو مرجعي لتسهيل المراجعة.'},
  {id:8, title:'AI Accounting Assistant', summary:'تحليل نص الفواتير، اقتراح قيود، وتلخيص مالي.', detail:'وظائف ai_parse_and_record_invoice و ai_generate_financial_summary لتسريع أعمال المحاسبة.'},
  {id:9, title:'واجهة المتجر الأمامية (Frontend Store Experience)', summary:'RTL عربي، تأثيرات neon، تجاوب كامل.', detail:'تجربة مستخدم متميزة، شبكة منتجات ديناميكية، أوضاع تجزئة وجملة.'},
  {id:10, title:'التقارير واللوحات التنفيذية (Reporting & Dashboards)', summary:'لوحات KPI وتقارير CSV/PDF.', detail:'ملخصات مالية، تقارير حضور، ومؤشرات أداء قابلة للتصدير.'}
];

const grid = document.getElementById('systemsGrid');
systems.forEach(s => {
  const div = document.createElement('div');
  div.className = 'card';
  div.setAttribute('data-id', s.id);
  div.innerHTML = `\n    <div class="num">${s.id}</div>\n    <h3>${s.title}</h3>\n    <p>${s.summary}</p>\n    <div class="meta">\n      <div class="chip">KPI: TBD</div>\n      <div class="chip">حالة: متقدم</div>\n    </div>\n  `;
  div.addEventListener('click', ()=> openDetail(s));
  grid.appendChild(div);
});

function openDetail(s){
  document.getElementById('detailPanel').classList.add('active');
  document.getElementById('detailTitle').textContent = s.title;
  document.getElementById('detailBody').innerHTML = `<p style="font-size:15px">${s.detail}</p><hr style="opacity:.08;margin:12px 0"/><p style="color:#9fc7ff">نقاط القيمة: <ul><li>قابلية التوسع</li><li>تكامل سهل مع موفري طرف ثالث</li><li>ترابط البيانات عبر الأنظمة</li></ul></p>`;
  window.scrollTo({top:0,behavior:'smooth'});
}
function closeDetail(){document.getElementById('detailPanel').classList.remove('active')}

</script>
