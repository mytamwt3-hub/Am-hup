import unittest
import json
import os
import re
from datetime import datetime, time
from decimal import Decimal, InvalidOperation, getcontext, ROUND_HALF_EVEN
from typing import Dict, List

# ضبط دقة عشرية مناسبة والـ rounding الافتراضي
getcontext().prec = 28
getcontext().rounding = ROUND_HALF_EVEN

CENT = Decimal('0.01')

# ملفات التخزين (داخل المستودع)
INVEST_DB_FILE = 'invest_db.json'
STORE_DB_FILE = 'store_db.json'

# سجلات عالمية
ACCOUNTS: Dict[str, 'Account'] = {}
FUNDINGS: List[Dict] = []
PURCHASES: List[Dict] = []
PRODUCTS: Dict[str, Dict] = {}
ORDERS: List[Dict] = []
SUBSCRIPTIONS: List[Dict] = []
INVENTORY: Dict[str, Dict[str, int]] = {}  # محطات المخزون (مثل '121') -> {product_code: qty}
CLOSED_REVENUES: List[Dict] = []
CCTV_INVOICE_LOGS: List[Dict] = []  # سجلات مزامنة الكاميرا والفواتير
ATTENDANCE_LOGS: List[Dict] = []  # سجلات البصمة اليومية الذكية
CHAT_MESSAGE_LOGS: List[Dict] = []  # سجلات المراسلة والدردشة الفورية
WHATSAPP_NOTIFICATIONS: List[Dict] = []  # سجلات إشعارات واتساب


def decimal_to_str(d: Decimal) -> str:
    return format(d.quantize(CENT, rounding=ROUND_HALF_EVEN), 'f')


def save_invest_db():
    data = {
        'wallets': [
            {
                'code': a.code,
                'name': a.name,
                'balance': decimal_to_str(a.balance),
                'nature': a.nature
            }
            for a in ACCOUNTS.values() if (a.code.startswith('115') or a.code.startswith('116') or a.code.startswith('117') or a.code.startswith('118') or a.code == '417')
        ],
        'fundings': FUNDINGS
    }
    with open(INVEST_DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def save_store_db():
    data = {
        'accounts': [
            {
                'code': a.code,
                'name': a.name,
                'balance': decimal_to_str(a.balance),
                'nature': a.nature,
                'parent': a.parent.code if a.parent else None
            }
            for a in ACCOUNTS.values() if (a.code.startswith('1') or a.code.startswith('11') or a.code.startswith('12') or a.code.startswith('113') or a.code == '417' or a.code.startswith('4'))
        ],
        'purchases': PURCHASES,
        'products': [
            {
                'code': pcode,
                'name': p['name'],
                'price': p['price'],
                'quantity': p['quantity']
            }
            for pcode, p in PRODUCTS.items()
        ],
        'orders': ORDERS,
        'subscriptions': SUBSCRIPTIONS,
        'inventory': INVENTORY,
        'closed_revenues': CLOSED_REVENUES,
        'cctv_invoice_logs': CCTV_INVOICE_LOGS,
        'attendance_logs': ATTENDANCE_LOGS,
        'chat_message_logs': CHAT_MESSAGE_LOGS,
        'whatsapp_notifications': WHATSAPP_NOTIFICATIONS
    }
    with open(STORE_DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def save_all_persistence():
    save_invest_db()
    save_store_db()


def load_invest_db():
    if not os.path.exists(INVEST_DB_FILE):
        return
    with open(INVEST_DB_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    for w in data.get('wallets', []):
        code = w['code']
        if code in ACCOUNTS:
            try:
                ACCOUNTS[code].balance = Decimal(w['balance'])
            except Exception:
                ACCOUNTS[code].balance = Decimal('0.00')
    FUNDINGS.clear()
    FUNDINGS.extend(data.get('fundings', []))


def load_store_db():
    if not os.path.exists(STORE_DB_FILE):
        return
    with open(STORE_DB_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    for a in data.get('accounts', []):
        code = a['code']
        if code in ACCOUNTS:
            try:
                ACCOUNTS[code].balance = Decimal(a['balance'])
            except Exception:
                ACCOUNTS[code].balance = Decimal('0.00')
    PURCHASES.clear()
    PURCHASES.extend(data.get('purchases', []))
    PRODUCTS.clear()
    for p in data.get('products', []):
        PRODUCTS[p['code']] = {'name': p['name'], 'price': p['price'], 'quantity': int(p['quantity'])}
    ORDERS.clear()
    ORDERS.extend(data.get('orders', []))
    SUBSCRIPTIONS.clear()
    SUBSCRIPTIONS.extend(data.get('subscriptions', []))
    INVENTORY.clear()
    INVENTORY.update(data.get('inventory', {}))
    CLOSED_REVENUES.clear()
    CLOSED_REVENUES.extend(data.get('closed_revenues', []))
    CCTV_INVOICE_LOGS.clear()
    CCTV_INVOICE_LOGS.extend(data.get('cctv_invoice_logs', []))
    ATTENDANCE_LOGS.clear()
    ATTENDANCE_LOGS.extend(data.get('attendance_logs', []))
    CHAT_MESSAGE_LOGS.clear()
    CHAT_MESSAGE_LOGS.extend(data.get('chat_message_logs', []))
    WHATSAPP_NOTIFICATIONS.clear()
    WHATSAPP_NOTIFICATIONS.extend(data.get('whatsapp_notifications', []))


class Account:
    def __init__(self, code: str, name: str, parent: 'Account' = None, nature: str = 'debit', is_temporary: bool = False):
        if nature not in ('debit', 'credit'):
            raise ValueError("الطبيعة يجب أن تكون 'debit' (مدين) أو 'credit' (دائن)")
        self.code = code
        self.name = name
        self.parent = parent
        self.nature = nature
        self.balance = Decimal('0.00')
        self.is_temporary = is_temporary
        # إضافة حقل الخصومات للموظفين
        self.deductions = Decimal('0.00')
        ACCOUNTS[self.code] = self

    def _apply_change(self, delta: Decimal):
        if not isinstance(delta, Decimal):
            raise TypeError("delta يجب أن يكون من نوع Decimal")
        self.balance += delta
        if self.parent:
            self.parent._apply_change(delta)

    def __repr__(self):
        return f"Account(code={self.code!r}, name={self.name!r}, nature={self.nature!r}, balance={self.balance}, deductions={self.deductions})"


class Entry:
    def __init__(self, account: Account, side: str, amount):
        if side not in ('debit', 'credit'):
            raise ValueError("الجانب يجب أن يكون 'debit' (مدين) أو 'credit' (دائن)")
        try:
            amt = Decimal(amount)
        except (InvalidOperation, TypeError):
            raise ValueError("المبلغ يجب أن يكون رقمياً صالحاً")
        if amt <= 0:
            raise ValueError("المبلغ يجب أن يكون موجباً")
        amt = amt.quantize(CENT, rounding=ROUND_HALF_EVEN)
        self.account = account
        self.side = side
        self.amount = amt

    def __repr__(self):
        return f"Entry(account={self.account.code!r}, side={self.side!r}, amount={self.amount})"


class Transaction:
    def __init__(self, description: str = ""):
        self.description = description
        self.entries: List[Entry] = []

    def add_entry(self, account: Account, side: str, amount):
        self.entries.append(Entry(account, side, amount))

    def commit(self):
        if not self.entries:
            raise ValueError("التسجيلة لا تحتوي على أطراف")

        total_debits = sum((e.amount for e in self.entries if e.side == 'debit'), Decimal('0.00'))
        total_credits = sum((e.amount for e in self.entries if e.side == 'credit'), Decimal('0.00'))

        if total_debits != total_credits:
            raise ValueError(f"المعاملة غير متزنة: المدين={total_debits} != الدائن={total_credits}")

        net_changes: Dict[Account, Decimal] = {}
        for e in self.entries:
            signed = e.amount if e.side == e.account.nature else -e.amount
            net_changes[e.account] = net_changes.get(e.account, Decimal('0.00')) + signed

        for account, delta in net_changes.items():
            account._apply_change(delta)

        save_all_persistence()


# ---------- نموذج الموظف/المستخدم/التاجر/الإدمن ----------
class Employee:
    def __init__(self, emp_id: str, name: str, base_salary: str, phone_number: str = None):
        self.emp_id = emp_id
        self.name = name
        self.base_salary = Decimal(base_salary).quantize(CENT, rounding=ROUND_HALF_EVEN)
        self.phone_number = phone_number
        self.deductions = Decimal('0.00')
        self.attendance_records = []

    def __repr__(self):
        return f"Employee(id={self.emp_id}, name={self.name}, salary={self.base_salary}, deductions={self.deductions})"


class Merchant:
    def __init__(self, merchant_id: str, name: str, role: str = 'Merchant', is_annual_subscription_paid: bool = False):
        self.merchant_id = merchant_id
        self.name = name
        self.role = role  # 'Admin' or 'Merchant'
        self.is_annual_subscription_paid = is_annual_subscription_paid

    def __repr__(self):
        return f"Merchant(id={self.merchant_id}, name={self.name}, role={self.role}, annual_paid={self.is_annual_subscription_paid})"


# ---------- نظام البصمة الذكي (Attendance System) ----------
def record_attendance_biometric(emp_id: str, employee: Employee, movement_type: str, time_str: str, date_str: str) -> Dict:
    """
    تسجيل بصمة الموظف (دخول/خروج) وحساب خصم التأخير تلقائياً
    
    Args:
        emp_id: معرف الموظف
        employee: كائن الموظف الذي يحتوي على الراتب الأساسي والهاتف
        movement_type: 'check_in' أو 'check_out'
        time_str: الساعة بصيغة "HH:MM" (مثال: "09:30")
        date_str: التاريخ بصيغة "YYYY-MM-DD"
    
    Returns:
        سجل البصمة مع الخصم المحسوب إن وجد
    """
    if movement_type not in ('check_in', 'check_out'):
        raise ValueError("نوع الحركة يجب أن تكون 'check_in' أو 'check_out'")
    
    # تحويل الوقت إلى كائن time
    try:
        att_time = datetime.strptime(time_str, "%H:%M").time()
    except ValueError:
        raise ValueError("صيغة الوقت غير صحيحة، استخدم HH:MM")
    
    # وقت الدوام الرسمي (الساعة 09:00 صباحاً)
    official_start = time(9, 0)
    
    deduction_amount = Decimal('0.00')
    is_late = False
    
    # إذا كانت بصمة دخول وتجاوزت الساعة 09:00
    if movement_type == 'check_in' and att_time > official_start:
        # حساب دقائق التأخير
        att_datetime = datetime.combine(datetime.today(), att_time)
        official_datetime = datetime.combine(datetime.today(), official_start)
        late_minutes = int((att_datetime - official_datetime).total_seconds() / 60)
        
        # معادلة الخصم: الراتب الأساسي / 30 يوم / 8 ساعات / 60 دقيقة
        per_minute_rate = employee.base_salary / 30 / 8 / 60
        deduction_amount = (per_minute_rate * Decimal(late_minutes)).quantize(CENT, rounding=ROUND_HALF_EVEN)
        
        # إضافة الخصم لحقل deductions الخاص بالموظف
        employee.deductions += deduction_amount
        is_late = True
    
    # سجل البصمة
    attendance_record = {
        'emp_id': emp_id,
        'emp_name': employee.name,
        'movement_type': movement_type,
        'time': time_str,
        'date': date_str,
        'timestamp': datetime.now().isoformat(),
        'is_late': is_late,
        'deduction_amount': decimal_to_str(deduction_amount),
        'employee_phone': employee.phone_number
    }
    
    ATTENDANCE_LOGS.append(attendance_record)
    save_all_persistence()
    
    return attendance_record


# ---------- نظام المراسلة والواتساب (Chat & WhatsApp Sync) ----------
def send_in_app_message(sender: str, receiver: str, text: str) -> Dict:
    """
    إرسال رسالة فورية داخل التطبيق بين الأطراف
    
    Args:
        sender: معرف المُرسل
        receiver: معرف المُستقبل
        text: نص الرسالة
    
    Returns:
        سجل الرسالة المحفوظة
    """
    message_record = {
        'sender': sender,
        'receiver': receiver,
        'text': text,
        'timestamp': datetime.now().isoformat(),
        'date': datetime.now().date().isoformat(),
        'time': datetime.now().time().strftime('%H:%M:%S'),
        'status': 'delivered'
    }
    
    CHAT_MESSAGE_LOGS.append(message_record)
    save_all_persistence()
    
    return message_record


def send_whatsapp_notification(recipient_phone: str, recipient_type: str, recipient_name: str, 
                               transaction_type: str, amount: str, invoice_id: str = None, 
                               employee_id: str = None) -> Dict:
    """
    محاكاة إرسال إشعار واتساب تلقائي بعد عملية بيع أو صرف راتب
    
    Args:
        recipient_phone: رقم هاتف المستلم (الزبون أو الموظف)
        recipient_type: 'customer' أو 'employee'
        recipient_name: اسم المستلم
        transaction_type: 'sale' أو 'salary'
        amount: المبلغ بصيغة Decimal
        invoice_id: رقم الفاتورة (في حالة البيع)
        employee_id: معرف الموظف (في حالة الراتب)
    
    Returns:
        سجل إرسال الإشعار
    """
    # صياغة الرسالة بناءً على النوع
    if transaction_type == 'sale':
        message_text = f"تم استلام طلبيتك برقم فاتورة {invoice_id}\nالمبلغ: {amount} ريال\nشكراً لتعاملك معنا 👍"
    elif transaction_type == 'salary':
        message_text = f"تم صرف راتبك برقم موظف {employee_id}\nالمبلغ: {amount} ريال\nشكراً لعملك معنا 💰"
    else:
        message_text = f"إشعار: تم تنفيذ عملية بمبلغ {amount} ريال"
    
    notification_record = {
        'recipient_phone': recipient_phone,
        'recipient_type': recipient_type,
        'recipient_name': recipient_name,
        'transaction_type': transaction_type,
        'amount': amount,
        'invoice_id': invoice_id,
        'employee_id': employee_id,
        'message_text': message_text,
        'timestamp': datetime.now().isoformat(),
        'date': datetime.now().date().isoformat(),
        'time': datetime.now().time().strftime('%H:%M:%S'),
        'status': 'Sent'
    }
    
    WHATSAPP_NOTIFICATIONS.append(notification_record)
    save_all_persistence()
    
    return notification_record


# ---------- وظائف المتجر الأساسية ----------
def add_product(code: str, name: str, price: str, quantity: int):
    """إضافة منتج جديد"""
    PRODUCTS[code] = {
        'name': name,
        'price': price,
        'quantity': quantity
    }


def renderStore() -> str:
    html = ['<div class="store">']
    for code, p in PRODUCTS.items():
        html.append(f"<div class=\"product\" data-code=\"{code}\">{p['name']} - السعر: {p['price']} - الكمية المتبقية: {p['quantity']}</div>")
    html.append('</div>')
    return '\n'.join(html)


def place_order(customer_account: Account, sales_account: Account, amount) -> Transaction:
    tx = Transaction(description=f"طلب متجر: {amount}")
    tx.add_entry(customer_account, 'debit', amount)
    tx.add_entry(sales_account, 'credit', amount)
    tx.commit()
    return tx


def sync_invoice_with_cctv(invoice_id: str, when: datetime):
    """
    محاكاة إرسال بيانات الفاتورة لسيرفر الكاميرا: نحفظ سجل يحتوي invoice_id والتاريخ والوقت ومقطع وهمي.
    يتم حفظه في CCTV_INVOICE_LOGS و persist فوراً.
    """
    entry = {
        'invoice_id': invoice_id,
        'date': when.date().isoformat(),
        'time': when.time().strftime('%H:%M:%S'),
        'video_ref': f"/cctv/streams/day_{when.date().isoformat()}.mp4#t={when.time().hour}h{when.time().minute}m{when.time().second}s"
    }
    CCTV_INVOICE_LOGS.append(entry)
    save_all_persistence()
    return entry


def admin_search_cctv_by_invoice(admin_user: Merchant, invoice_id: str = None, date_str: str = None) -> List[Dict]:
    if admin_user.role != 'Admin':
        raise PermissionError('المستخدم ليس إدمن للوصول لسجلات الكاميرا')
    results = []
    for e in CCTV_INVOICE_LOGS:
        if invoice_id and e.get('invoice_id') == invoice_id:
            results.append(e)
        elif date_str and e.get('date') == date_str:
            results.append(e)
    return results


def buyFromStore(product_code: str, quantity: int, customer_account: Account, sales_account: Account, 
                 customer_phone: str = None, inventory_station: str = '121') -> Dict:
    if product_code not in PRODUCTS:
        raise ValueError('المنتج غير موجود')
    if quantity <= 0:
        raise ValueError('الكمية يجب أن تكون موجبة')
    prod = PRODUCTS[product_code]
    if prod['quantity'] < quantity:
        raise ValueError('الكمية غير متوفرة في المخزون')
    price = Decimal(prod['price'])
    total = (price * Decimal(quantity)).quantize(CENT, rounding=ROUND_HALF_EVEN)

    # سجل الطلب (العميل مدين، المبيعات دائن)
    place_order(customer_account, sales_account, total)

    # اقتطاع عمولة المنصة 5%
    platform = ACCOUNTS.get('417') or Account('417', 'عمولة_المنصة', nature='credit')
    platform_fee = (total * Decimal('0.05')).quantize(CENT, rounding=ROUND_HALF_EVEN)
    fee_tx = Transaction(description=f"عمولة منصة على بيع {product_code}: {platform_fee}")
    fee_tx.add_entry(sales_account, 'debit', platform_fee)
    fee_tx.add_entry(platform, 'credit', platform_fee)
    fee_tx.commit()

    # نقص الكمية فوراً من المنتجات والمخزن اللحظي
    prod['quantity'] -= int(quantity)
    INVENTORY.setdefault(inventory_station, {})
    INVENTORY[inventory_station].setdefault(product_code, 0)
    INVENTORY[inventory_station][product_code] = INVENTORY[inventory_station][product_code] - int(quantity)

    # إنشاء invoice id
    invoice_id = f"INV{len(ORDERS)+1:06d}"
    now = datetime.now()

    # سجل الطلب
    order = {'invoice_id': invoice_id, 'product': product_code, 'quantity': int(quantity), 'total': decimal_to_str(total), 
             'platform_fee': decimal_to_str(platform_fee), 'status': 'new', 'created_at': now.isoformat(), 'customer_phone': customer_phone}
    ORDERS.append(order)
    PURCHASES.append({'product': product_code, 'quantity': int(quantity), 'amount': decimal_to_str(total)})

    save_all_persistence()

    # محاكاة حالة الطلب تلقائياً
    order['status'] = 'preparing'
    order['status'] = 'shipped'
    order['status'] = 'delivered'

    # بعد إتمام البيع ندفع تسجيل إلى نظام الكاميرا
    sync_invoice_with_cctv(invoice_id, now)

    # إرسال إشعار واتساب تلقائي إذا تم توفير رقم الهاتف
    if customer_phone:
        send_whatsapp_notification(
            recipient_phone=customer_phone,
            recipient_type='customer',
            recipient_name='العميل',
            transaction_type='sale',
            amount=decimal_to_str(total),
            invoice_id=invoice_id
        )

    save_all_persistence()
    return order


def pay_salary(employee: Employee, salary_amount: str) -> Dict:
    """
    صرف راتب الموظف مع محاسبة الخصومات وإرسال إشعار واتساب
    
    Args:
        employee: كائن الموظف
        salary_amount: المبلغ المراد صرفه
    
    Returns:
        سجل صرف الراتب
    """
    try:
        amount = Decimal(salary_amount).quantize(CENT, rounding=ROUND_HALF_EVEN)
    except (InvalidOperation, TypeError):
        raise ValueError("المبلغ يجب أن يكون رقمياً صالحاً")
    
    # سجل صرف الراتب
    salary_record = {
        'emp_id': employee.emp_id,
        'emp_name': employee.name,
        'base_salary': decimal_to_str(employee.base_salary),
        'deductions': decimal_to_str(employee.deductions),
        'net_salary': decimal_to_str(amount - employee.deductions),
        'timestamp': datetime.now().isoformat(),
        'date': datetime.now().date().isoformat(),
        'time': datetime.now().time().strftime('%H:%M:%S'),
        'status': 'paid'
    }
    
    # إرسال إشعار واتساب تلقائي إذا توفر رقم الهاتف
    if employee.phone_number:
        send_whatsapp_notification(
            recipient_phone=employee.phone_number,
            recipient_type='employee',
            recipient_name=employee.name,
            transaction_type='salary',
            amount=decimal_to_str(amount - employee.deductions),
            employee_id=employee.emp_id
        )
    
    return salary_record


def execute_financial_closing(admin: Merchant, merchant: Merchant) -> bool:
    """إغلاق مالي للفترة"""
    if admin.role != 'Admin':
        raise PermissionError('ليس لديك صلاحيات الإدمن')
    
    if not merchant.is_annual_subscription_paid:
        raise ValueError('لا يمكن إتمام الإقفال المالي مالم يتم سداد قيمة الباقة السنوية للمنصة أولاً')
    
    # إغلاق حسابات مؤقتة وتسجيل الإيرادات المقفلة
    platform = ACCOUNTS.get('417')
    if platform and platform.balance > 0:
        revenue_record = {'merchant_id': merchant.merchant_id, 'amount': decimal_to_str(platform.balance)}
        CLOSED_REVENUES.append(revenue_record)
        platform.balance = Decimal('0.00')
    
    # إعادة تعيين الحسابات المؤقتة
    for acc in ACCOUNTS.values():
        if acc.is_temporary:
            acc.balance = Decimal('0.00')
    
    save_all_persistence()
    return True


# ---------- AI Accountant Agent (محاسب ذكي) ----------
def ai_parse_and_record_invoice(text: str, target_inventory_station: str = '121') -> Dict:
    """
    تحاكي قراءة نص فاتورة مشتريات، وتستخرج الكمية/المبلغ/باركود المنتج وتولد قيد محاسبي مناسب
    """
    # بحث عن مبلغ
    m = re.search(r"(\d+[\.,]?\d*)", text)
    if not m:
        raise ValueError('لم يتم العثور على مبلغ في النص')
    amount = Decimal(m.group(1).replace(',', '.')).quantize(CENT, rounding=ROUND_HALF_EVEN)

    # بحث عن باركود
    p = re.search(r"P\d+", text)
    product_code = p.group(0) if p else None

    # تأكد من حسابات أساسية
    cash = ACCOUNTS.get('111') or Account('111', 'الصندوق', nature='debit')
    inventory_acc = ACCOUNTS.get('121') or Account('121', 'المخزن_اللحظي', nature='debit')
    supplier = ACCOUNTS.get('211') or Account('211', 'دائنون_الموردين', nature='credit')

    # اختَر نوع القيد
    if cash.balance >= amount:
        # قيد مشتريات من الصندوق: مدين للمخزون، دائن للصندوق
        tx = Transaction(description=f"AI: قيد شراء نقدي {product_code or ''} {amount}")
        tx.add_entry(inventory_acc, 'debit', amount)
        tx.add_entry(cash, 'credit', amount)
        tx.commit()
        method = 'cash'
    else:
        # قيد مشتريات ممول: مدين للمخزون، دائن للمورد
        tx = Transaction(description=f"AI: قيد شراء ممول {product_code or ''} {amount}")
        tx.add_entry(inventory_acc, 'debit', amount)
        tx.add_entry(supplier, 'credit', amount)
        tx.commit()
        method = 'funded'

    # حدس الكمية: إذا كان المنتج معروفاً نستخدم السعر لإيجاد كمية تقريبية
    qty_added = 0
    if product_code and product_code in PRODUCTS:
        price = Decimal(PRODUCTS[product_code]['price'])
        try:
            qty_added = int((amount / price).to_integral_value(rounding=ROUND_HALF_EVEN))
        except Exception:
            qty_added = 0
        if qty_added <= 0:
            qty_added = 1
        PRODUCTS[product_code]['quantity'] += qty_added
        INVENTORY.setdefault(target_inventory_station, {})
        INVENTORY[target_inventory_station][product_code] = INVENTORY[target_inventory_station].get(product_code, 0) + qty_added
        save_all_persistence()

    result = {'amount': decimal_to_str(amount), 'product': product_code, 'qty_added': qty_added, 'method': method}
    return result


def ai_generate_financial_summary() -> Dict:
    """
    يقرأ الأرصدة من ACCOUNTS ويولد ملخصاً بسيطاً
    """
    # حاول إعادة تحميل القيم من الملفات إن وجدت
    load_invest_db()
    load_store_db()

    total_assets = Decimal('0.00')
    for acc in ACCOUNTS.values():
        if acc.nature == 'debit':
            total_assets += acc.balance

    cash111 = ACCOUNTS.get('111').balance if '111' in ACCOUNTS else Decimal('0.00')
    wallet116 = ACCOUNTS.get('116').balance if '116' in ACCOUNTS else Decimal('0.00')
    platform417 = ACCOUNTS.get('417').balance if '417' in ACCOUNTS else Decimal('0.00')

    summary = {
        'total_assets': decimal_to_str(total_assets),
        'cash_111': decimal_to_str(cash111),
        'merchant_wallet_116': decimal_to_str(wallet116),
        'platform_commissions_417': decimal_to_str(platform417)
    }
    return summary


# ---------- اختبارات الوحدة النهائية (محدثة مع البصمة والواتساب) ----------
class TestMetaHubAccounting(unittest.TestCase):
    def setUp(self):
        # حذف ملفات التخزين إن وجدت لضمان بيئة اختبار نظيفة
        for fname in (INVEST_DB_FILE, STORE_DB_FILE):
            try:
                os.remove(fname)
            except OSError:
                pass
        ACCOUNTS.clear()
        FUNDINGS.clear()
        PURCHASES.clear()
        PRODUCTS.clear()
        ORDERS.clear()
        SUBSCRIPTIONS.clear()
        INVENTORY.clear()
        CLOSED_REVENUES.clear()
        CCTV_INVOICE_LOGS.clear()
        ATTENDANCE_LOGS.clear()
        CHAT_MESSAGE_LOGS.clear()
        WHATSAPP_NOTIFICATIONS.clear()

        # حسابات أساسية
        assets = Account('1', 'الأصول', nature='debit')
        self.cash = Account('111', 'الصندوق', parent=assets, nature='debit')
        self.sales = Account('411', 'مبيعات_متجر', nature='credit')
        self.platform = Account('417', 'عمولة_المنصة', nature='credit')
        self.inventory_account = Account('121', 'المخزن_اللحظي', nature='debit')
        self.distribution_expense = Account('599', 'مصاريف_توزيع', nature='debit', is_temporary=True)

        # عينات منتجات
        add_product('P001', 'جوال', '150.00', 10)
        add_product('P002', 'ساعة', '50.00', 20)

    def test_buy_reduces_product_and_inventory_121(self):
        customer = Account('113', 'عملاء_متجر', nature='debit')
        order = buyFromStore('P001', 2, customer, self.sales)
        self.assertEqual(PRODUCTS['P001']['quantity'], 8)
        self.assertEqual(INVENTORY['121']['P001'], 8)

        # buy another product
        buyFromStore('P002', 3, customer, self.sales)
        self.assertEqual(PRODUCTS['P002']['quantity'], 17)
        self.assertEqual(INVENTORY['121']['P002'], 17)

    def test_financial_closing_rejected_if_annual_not_paid(self):
        admin = Merchant('A01', 'super', role='Admin')
        merchant = Merchant('M01', 'StoreOne', role='Merchant', is_annual_subscription_paid=False)
        self.platform.balance = Decimal('50.00')
        with self.assertRaises(ValueError) as cm:
            execute_financial_closing(admin, merchant)
        self.assertEqual(str(cm.exception), 'لا يمكن إتمام الإقفال المالي مالم يتم سداد قيمة الباقة السنوية للمنصة أولاً')
        self.assertEqual(self.platform.balance, Decimal('50.00'))

    def test_financial_closing_success_if_paid_and_zero_accounts(self):
        admin = Merchant('A01', 'super', role='Admin')
        merchant = Merchant('M01', 'StoreOne', role='Merchant', is_annual_subscription_paid=True)
        self.platform.balance = Decimal('111.50')
        self.distribution_expense.balance = Decimal('10.00')
        res = execute_financial_closing(admin, merchant)
        self.assertTrue(res)
        self.assertEqual(self.platform.balance, Decimal('0.00'))
        self.assertIn({'merchant_id': 'M01', 'amount': '111.50'}, CLOSED_REVENUES)
        self.assertEqual(self.distribution_expense.balance, Decimal('0.00'))

    def test_ai_accountant_agent(self):
        self.cash.balance = Decimal('0.00')
        before_qty = PRODUCTS['P001']['quantity']
        text = 'فاتورة شراء من مورد الأجهزة بقيمة 500 ريال وباركود P001'
        result = ai_parse_and_record_invoice(text)
        self.assertEqual(result['product'], 'P001')
        self.assertTrue(Decimal(result['amount']) > 0)
        self.assertTrue(result['qty_added'] >= 1)
        self.assertEqual(PRODUCTS['P001']['quantity'], before_qty + result['qty_added'])

        summary = ai_generate_financial_summary()
        self.assertIn('total_assets', summary)
        self.assertIn('cash_111', summary)
        self.assertIn('merchant_wallet_116', summary)
        self.assertIn('platform_commissions_417', summary)
        Decimal(summary['total_assets'])
        Decimal(summary['cash_111'])

    def test_cctv_invoice_synchronization(self):
        customer = Account('113', 'عملاء_متجر', nature='debit')
        order = buyFromStore('P001', 1, customer, self.sales)
        invoice_id = order['invoice_id']
        found = [e for e in CCTV_INVOICE_LOGS if e.get('invoice_id') == invoice_id]
        self.assertTrue(len(found) == 1)
        entry = found[0]
        self.assertIn('date', entry)
        self.assertIn('time', entry)
        self.assertIn('video_ref', entry)

        admin = Merchant('A01', 'super', role='Admin')
        res = admin_search_cctv_by_invoice(admin, invoice_id=invoice_id)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]['invoice_id'], invoice_id)

    def test_biometric_attendance_and_whatsapp_chat(self):
        """
        اختبار شامل لنظام البصمة الذكي وإرسال إشعارات الواتساب
        يتأكد من أن تسجيل بصمة موظف متأخر يحسب الخصم بدقة ويضيفه لخصوماته
        """
        # إنشاء موظف
        employee = Employee('E001', 'أحمد محمد', '3000.00', '+966501234567')
        
        # اختبار الحالة الأولى: بصمة دخول متأخرة (09:30)
        att_record = record_attendance_biometric(
            emp_id='E001',
            employee=employee,
            movement_type='check_in',
            time_str='09:30',
            date_str='2026-09-03'
        )
        
        # التحقق من أن البصمة تم تسجيلها بنجاح
        self.assertEqual(att_record['emp_id'], 'E001')
        self.assertEqual(att_record['movement_type'], 'check_in')
        self.assertEqual(att_record['time'], '09:30')
        self.assertTrue(att_record['is_late'])
        
        # حساب الخصم المتوقع:
        # الراتب الأساسي = 3000 ريال
        # معادلة الخصم: الراتب / 30 يوم / 8 ساعات / 60 دقيقة
        # = 3000 / 30 / 8 / 60 = 0.208333... ريال/دقيقة
        # دقائق التأخير = 30 دقيقة
        # الخصم = 0.208333 * 30 = 6.25 ريال
        expected_deduction = Decimal('6.25')
        actual_deduction = Decimal(att_record['deduction_amount'])
        self.assertEqual(actual_deduction, expected_deduction)
        
        # التحقق من إضافة الخصم لحقل deductions الخاص بالموظف
        self.assertEqual(employee.deductions, expected_deduction)
        
        # التحقق من حفظ السجل في ATTENDANCE_LOGS
        self.assertEqual(len(ATTENDANCE_LOGS), 1)
        self.assertIn(att_record, ATTENDANCE_LOGS)
        
        # اختبار الحالة الثانية: بصمة خروج (لا خصم)
        att_checkout = record_attendance_biometric(
            emp_id='E001',
            employee=employee,
            movement_type='check_out',
            time_str='17:30',
            date_str='2026-09-03'
        )
        
        self.assertFalse(att_checkout['is_late'])
        self.assertEqual(att_checkout['deduction_amount'], '0.00')
        self.assertEqual(employee.deductions, expected_deduction)  # لم يتغير
        
        # اختبار الحالة الثالثة: بصمة دخول بدون تأخير (09:00)
        employee2 = Employee('E002', 'فاطم�� علي', '2500.00', '+966501234568')
        att_on_time = record_attendance_biometric(
            emp_id='E002',
            employee=employee2,
            movement_type='check_in',
            time_str='09:00',
            date_str='2026-09-03'
        )
        
        self.assertFalse(att_on_time['is_late'])
        self.assertEqual(att_on_time['deduction_amount'], '0.00')
        self.assertEqual(employee2.deductions, Decimal('0.00'))

    def test_whatsapp_notifications_on_sale_and_salary(self):
        """
        اختبار إرسال إشعارات الواتساب تلقائياً عند البيع وصرف الراتب
        يتأكد من توليد سجل إرسال الإشعار بنجاح ودون أخطاء
        """
        # اختبار الحالة الأولى: إرسال إشعار واتساب على عملية بيع
        customer = Account('113', 'عملاء_متجر', nature='debit')
        order = buyFromStore(
            'P001', 1, customer, self.sales,
            customer_phone='+966501111111'
        )
        
        # التحقق من أن الإشعار تم إرساله
        sale_notifications = [n for n in WHATSAPP_NOTIFICATIONS if n['transaction_type'] == 'sale']
        self.assertEqual(len(sale_notifications), 1)
        notification = sale_notifications[0]
        
        # التحقق من محتوى الإشعار
        self.assertEqual(notification['recipient_type'], 'customer')
        self.assertEqual(notification['recipient_phone'], '+966501111111')
        self.assertEqual(notification['status'], 'Sent')
        self.assertIn(order['invoice_id'], notification['message_text'])
        
        # اختبار الحالة الثانية: إرسال إشعار واتساب عند صرف الراتب
        employee = Employee('E001', 'أحمد محمد', '3000.00', '+966502222222')
        employee.deductions = Decimal('6.25')  # إضافة خصم سابق
        
        salary_record = pay_salary(employee, '2993.75')  # الراتب بعد الخصم
        
        # التحقق من أن الإشعار تم إرساله
        salary_notifications = [n for n in WHATSAPP_NOTIFICATIONS if n['transaction_type'] == 'salary']
        self.assertEqual(len(salary_notifications), 1)
        salary_notif = salary_notifications[0]
        
        # التحقق من محتوى إشعار الراتب
        self.assertEqual(salary_notif['recipient_type'], 'employee')
        self.assertEqual(salary_notif['recipient_phone'], '+966502222222')
        self.assertEqual(salary_notif['recipient_name'], 'أحمد محمد')
        self.assertEqual(salary_notif['status'], 'Sent')
        self.assertIn(employee.emp_id, salary_notif['message_text'])

    def test_in_app_messaging(self):
        """
        اختبار نظام المراسلة الفورية داخل التطبيق
        """
        # إرسال رسالة بين مستخدمين
        message = send_in_app_message(
            sender='user001',
            receiver='user002',
            text='السلام عليكم ورحمة الله وبركاته، كيف حالك؟'
        )
        
        # التحقق من محتوى الرسالة
        self.assertEqual(message['sender'], 'user001')
        self.assertEqual(message['receiver'], 'user002')
        self.assertEqual(message['status'], 'delivered')
        self.assertIn('timestamp', message)
        self.assertIn('time', message)
        
        # التحقق من حفظ الرسالة
        self.assertEqual(len(CHAT_MESSAGE_LOGS), 1)
        self.assertIn(message, CHAT_MESSAGE_LOGS)
        
        # إرسال رسالة أخرى
        message2 = send_in_app_message(
            sender='user002',
            receiver='user001',
            text='وعليكم السلام ورحمة الله وبركاته، تمام الحمد لله'
        )
        
        # التحقق من الرسالة الثانية
        self.assertEqual(len(CHAT_MESSAGE_LOGS), 2)
        self.assertEqual(CHAT_MESSAGE_LOGS[1]['sender'], 'user002')


if __name__ == '__main__':
    load_invest_db()
    load_store_db()
    unittest.main(verbosity=2)
