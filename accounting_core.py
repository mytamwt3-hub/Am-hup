"""
accounting_core.py
Modified: call investments.allocate_sale_for_order after placing an order (local import to avoid circular import)
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

# rest of file unchanged until buyFromStore

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
    INVENTORY[inventory_station][product_code] = INVENTORY[inventory_station].get(product_code, 0) - int(quantity)

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

    # allocate to investments (if any)
    try:
        from investments import allocate_sale_for_order
        allocate_sale_for_order(order)
    except Exception:
        pass

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

# rest of file unchanged
