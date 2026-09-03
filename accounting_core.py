"""
accounting_core.py
النواة المحاسبية الكاملة لـ MetaHOP
- نظام الحسابات المحاسبي مع Decimal
- نظام البصمة الذكي
- نظام المراسلة والواتساب
- نظام الكاميرات CCTV
- نظام المنتجات والمخزون
"""

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

# ملفات التخزين
INVEST_DB_FILE = 'invest_db.json'
STORE_DB_FILE = 'store_db.json'

# سجلات عالمية
ACCOUNTS: Dict[str, 'Account'] = {}
FUNDINGS: List[Dict] = []
PURCHASES: List[Dict] = []
PRODUCTS: Dict[str, Dict] = {}
ORDERS: List[Dict] = []
SUBSCRIPTIONS: List[Dict] = []
INVENTORY: Dict[str, Dict[str, int]] = {}
CLOSED_REVENUES: List[Dict] = []
CCTV_INVOICE_LOGS: List[Dict] = []
ATTENDANCE_LOGS: List[Dict] = []
CHAT_MESSAGE_LOGS: List[Dict] = []
WHATSAPP_NOTIFICATIONS: List[Dict] = []


def decimal_to_str(d: Decimal) -> str:
    """تحويل Decimal إلى نص مقرب بالهللة"""
    return format(d.quantize(CENT, rounding=ROUND_HALF_EVEN), 'f')


def save_invest_db():
    """حفظ ملف محافظ الاستثمار"""
    data = {
        'wallets': [
            {
                'code': a.code,
                'name': a.name,
                'balance': decimal_to_str(a.balance),
                'nature': a.nature
            }
            for a in ACCOUNTS.values() if (a.code.startswith('115') or a.code.startswith('116') or 
                                          a.code.startswith('117') or a.code.startswith('118') or a.code == '417')
        ],
        'fundings': FUNDINGS
    }
    with open(INVEST_DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def save_store_db():
    """حفظ ملف المتجر الشامل"""
    data = {
        'accounts': [
            {
                'code': a.code,
                'name': a.name,
                'balance': decimal_to_str(a.balance),
                'nature': a.nature,
                'parent': a.parent.code if a.parent else None
            }
            for a in ACCOUNTS.values() if (a.code.startswith('1') or a.code.startswith('11') or 
                                          a.code.startswith('12') or a.code.startswith('113') or 
                                          a.code == '417' or a.code.startswith('4'))
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
    """حفظ جميع البيانات"""
    save_invest_db()
    save_store_db()


def load_invest_db():
    """تحميل ملف محافظ الاستثمار"""
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
    """تحميل ملف المتجر الشامل"""
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


# ========== Classes ==========

class Account:
    """حساب محاسبي"""
    def __init__(self, code: str, name: str, parent: 'Account' = None, nature: str = 'debit', is_temporary: bool = False):
        if nature not in ('debit', 'credit'):
            raise ValueError("الطبيعة يجب أن تكون 'debit' (مدين) أو 'credit' (دائن)")
        self.code = code
        self.name = name
        self.parent = parent
        self.nature = nature
        self.balance = Decimal('0.00')
        self.is_temporary = is_temporary
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
    """قيد محاسبي منفرد"""
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
    """معاملة محاسبية متوازنة"""
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


class Employee:
    """نموذج الموظف"""
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
    """نموذج التاجر/المدير"""
    def __init__(self, merchant_id: str, name: str, role: str = 'Merchant', is_annual_subscription_paid: bool = False):
        self.merchant_id = merchant_id
        self.name = name
        self.role = role
        self.is_annual_subscription_paid = is_annual_subscription_paid

    def __repr__(self):
        return f"Merchant(id={self.merchant_id}, name={self.name}, role={self.role}, annual_paid={self.is_annual_subscription_paid})"


# ========== وظائف المنتجات والمتجر ==========

def add_product(code: str, name: str, price: str, quantity: int):
    """إضافة منتج جديد"""
    PRODUCTS[code] = {
        'name': name,
        'price': price,
        'quantity': quantity
    }


def get_products() -> List[Dict]:
    """الحصول على قائمة المنتجات"""
    return [
        {
            'code': code,
            'name': p['name'],
            'price': p['price'],
            'quantity': p['quantity']
        }
        for code, p in PRODUCTS.items()
    ]


def place_order(customer_account: Account, sales_account: Account, amount) -> Transaction:
    """تسجيل طلب"""
    tx = Transaction(description=f"طلب متجر: {amount}")
    tx.add_entry(customer_account, 'debit', amount)
    tx.add_entry(sales_account, 'credit', amount)
    tx.commit()
    return tx


def buyFromStore(product_code: str, quantity: int, customer_account: Account, sales_account: Account, 
                 customer_phone: str = None, inventory_station: str = '121') -> Dict:
    """شراء من المتجر مع تسجيل قيد وإشعار واتساب"""
    if product_code not in PRODUCTS:
        raise ValueError('المنتج غير موجود')
    if quantity <= 0:
        raise ValueError('الكمية يجب أن تكون موجبة')
    prod = PRODUCTS[product_code]
    if prod['quantity'] < quantity:
        raise ValueError('الكمية غير متوفرة في المخزون')
    
    price = Decimal(prod['price'])
    total = (price * Decimal(quantity)).quantize(CENT, rounding=ROUND_HALF_EVEN)

    # تسجيل الطلب
    place_order(customer_account, sales_account, total)

    # عمولة المنصة 5%
    platform = ACCOUNTS.get('417') or Account('417', 'عمولة_المنصة', nature='credit')
    platform_fee = (total * Decimal('0.05')).quantize(CENT, rounding=ROUND_HALF_EVEN)
    fee_tx = Transaction(description=f"عمولة منصة على بيع {product_code}: {platform_fee}")
    fee_tx.add_entry(sales_account, 'debit', platform_fee)
    fee_tx.add_entry(platform, 'credit', platform_fee)
    fee_tx.commit()

    # تحديث المخزون
    prod['quantity'] -= int(quantity)
    INVENTORY.setdefault(inventory_station, {})
    INVENTORY[inventory_station].setdefault(product_code, 0)
    INVENTORY[inventory_station][product_code] = INVENTORY[inventory_station][product_code] - int(quantity)

    # إنشاء رقم فاتورة
    invoice_id = f"INV{len(ORDERS)+1:06d}"
    now = datetime.now()

    # حفظ الطلب
    order = {
        'invoice_id': invoice_id,
        'product': product_code,
        'quantity': int(quantity),
        'total': decimal_to_str(total),
        'platform_fee': decimal_to_str(platform_fee),
        'status': 'delivered',
        'created_at': now.isoformat(),
        'customer_phone': customer_phone
    }
    ORDERS.append(order)
    PURCHASES.append({'product': product_code, 'quantity': int(quantity), 'amount': decimal_to_str(total)})

    save_all_persistence()

    # مزامنة الكاميرا
    sync_invoice_with_cctv(invoice_id, now)

    # إشعار واتساب
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


# ========== نظام الكاميرات CCTV ==========

def sync_invoice_with_cctv(invoice_id: str, when: datetime):
    """مزامنة الفاتورة مع سجل الكاميرا"""
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
    """البحث في سجلات الكاميرا"""
    if admin_user.role != 'Admin':
        raise PermissionError('المستخدم ليس إدمن للوصول لسجلات الكاميرا')
    results = []
    for e in CCTV_INVOICE_LOGS:
        if invoice_id and e.get('invoice_id') == invoice_id:
            results.append(e)
        elif date_str and e.get('date') == date_str:
            results.append(e)
    return results


# ========== نظام البصمة الذكي ==========

def record_attendance_biometric(emp_id: str, employee: Employee, movement_type: str, time_str: str, date_str: str) -> Dict:
    """تسجيل بصمة موظف مع حساب خصم التأخير التلقائي"""
    if movement_type not in ('check_in', 'check_out'):
        raise ValueError("نوع الحركة يجب أن تكون 'check_in' أو 'check_out'")
    
    try:
        att_time = datetime.strptime(time_str, "%H:%M").time()
    except ValueError:
        raise ValueError("صيغة الوقت غير صحيحة، استخدم HH:MM")
    
    official_start = time(9, 0)
    deduction_amount = Decimal('0.00')
    is_late = False
    
    if movement_type == 'check_in' and att_time > official_start:
        att_datetime = datetime.combine(datetime.today(), att_time)
        official_datetime = datetime.combine(datetime.today(), official_start)
        late_minutes = int((att_datetime - official_datetime).total_seconds() / 60)
        
        per_minute_rate = employee.base_salary / 30 / 8 / 60
        deduction_amount = (per_minute_rate * Decimal(late_minutes)).quantize(CENT, rounding=ROUND_HALF_EVEN)
        
        employee.deductions += deduction_amount
        is_late = True
    
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


def pay_salary(employee: Employee, salary_amount: str) -> Dict:
    """صرف راتب موظف مع إشعار واتساب"""
    try:
        amount = Decimal(salary_amount).quantize(CENT, rounding=ROUND_HALF_EVEN)
    except (InvalidOperation, TypeError):
        raise ValueError("المبلغ يجب أن يكون رقمياً صالحاً")
    
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


# ========== نظام المراسلة والواتساب ==========

def send_in_app_message(sender: str, receiver: str, text: str) -> Dict:
    """إرسال رسالة فورية داخل التطبيق"""
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
    """إرسال إشعار واتساب تلقائي"""
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


# ========== وظائف الإقفال المالي ==========

def execute_financial_closing(admin: Merchant, merchant: Merchant) -> bool:
    """إغلاق مالي للفترة"""
    if admin.role != 'Admin':
        raise PermissionError('ليس لديك صلاحيات الإدمن')
    
    if not merchant.is_annual_subscription_paid:
        raise ValueError('لا يمكن إتمام الإقفال المالي مالم يتم سداد قيمة الباقة السنوية للمنصة أولاً')
    
    platform = ACCOUNTS.get('417')
    if platform and platform.balance > 0:
        revenue_record = {'merchant_id': merchant.merchant_id, 'amount': decimal_to_str(platform.balance)}
        CLOSED_REVENUES.append(revenue_record)
        platform.balance = Decimal('0.00')
    
    for acc in ACCOUNTS.values():
        if acc.is_temporary:
            acc.balance = Decimal('0.00')
    
    save_all_persistence()
    return True


# ========== وكيل المحاسب الذكي ==========

def ai_parse_and_record_invoice(text: str, target_inventory_station: str = '121') -> Dict:
    """تحليل وتسجيل فاتورة مشتريات"""
    m = re.search(r"(\d+[\.,]?\d*)", text)
    if not m:
        raise ValueError('لم يتم العثور على مبلغ في النص')
    amount = Decimal(m.group(1).replace(',', '.')).quantize(CENT, rounding=ROUND_HALF_EVEN)

    p = re.search(r"P\d+", text)
    product_code = p.group(0) if p else None

    cash = ACCOUNTS.get('111') or Account('111', 'الصندوق', nature='debit')
    inventory_acc = ACCOUNTS.get('121') or Account('121', 'المخزن_اللحظي', nature='debit')
    supplier = ACCOUNTS.get('211') or Account('211', 'دائنون_الموردين', nature='credit')

    if cash.balance >= amount:
        tx = Transaction(description=f"AI: قيد شراء نقدي {product_code or ''} {amount}")
        tx.add_entry(inventory_acc, 'debit', amount)
        tx.add_entry(cash, 'credit', amount)
        tx.commit()
        method = 'cash'
    else:
        tx = Transaction(description=f"AI: قيد شراء ممول {product_code or ''} {amount}")
        tx.add_entry(inventory_acc, 'debit', amount)
        tx.add_entry(supplier, 'credit', amount)
        tx.commit()
        method = 'funded'

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
    """توليد ملخص مالي شامل"""
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
