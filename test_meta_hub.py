import unittest
import json
import os
from decimal import Decimal, InvalidOperation, getcontext, ROUND_HALF_EVEN
from typing import Dict, List

# ضبط دقة عشرية مناسبة والـ rounding الافتراضي
getcontext().prec = 28
getcontext().rounding = ROUND_HALF_EVEN

CENT = Decimal('0.01')

# ملفات التخزين (داخل المستودع)
INVEST_DB_FILE = 'invest_db.json'
STORE_DB_FILE = 'store_db.json'

# سجل عالمي للحسابات ولعمليات التمويل/المشتريات
ACCOUNTS: Dict[str, 'Account'] = {}
FUNDINGS: List[Dict] = []
PURCHASES: List[Dict] = []
PRODUCTS: Dict[str, Dict] = {}
ORDERS: List[Dict] = []


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
            for a in ACCOUNTS.values() if a.code.startswith('115') or a.code.startswith('116') or a.code.startswith('117') or a.code.startswith('118')
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
            for a in ACCOUNTS.values() if a.code.startswith('1') or a.code.startswith('11') or a.code.startswith('12') or a.code.startswith('113')
        ],
        'purchases': PURCHASES,
        'products': [
            {
                'code': pcode,
                'name': p['name'],
                'price': decimal_to_str(Decimal(p['price'])),
                'quantity': p['quantity']
            }
            for pcode, p in PRODUCTS.items()
        ],
        'orders': ORDERS
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
    # load fundings
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
    # load purchases
    PURCHASES.clear()
    PURCHASES.extend(data.get('purchases', []))
    # load products
    PRODUCTS.clear()
    for p in data.get('products', []):
        PRODUCTS[p['code']] = {'name': p['name'], 'price': decimal_to_str(Decimal(p['price'])), 'quantity': int(p['quantity'])}
    ORDERS.clear()
    ORDERS.extend(data.get('orders', []))


class Account:
    def __init__(self, code: str, name: str, parent: 'Account' = None, nature: str = 'debit'):
        if nature not in ('debit', 'credit'):
            raise ValueError("الطبيعة يجب أن تكون 'debit' (مدين) أو 'credit' (دائن)")
        self.code = code
        self.name = name
        self.parent = parent
        self.nature = nature
        self.balance = Decimal('0.00')
        ACCOUNTS[self.code] = self

    def _apply_change(self, delta: Decimal):
        if not isinstance(delta, Decimal):
            raise TypeError("delta يجب أن يكون من نوع Decimal")
        self.balance += delta
        if self.parent:
            self.parent._apply_change(delta)

    def __repr__(self):
        return f"Account(code={self.code!r}, name={self.name!r}, nature={self.nature!r}, balance={self.balance})"


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


# ---------- نظام شؤون الموظفين والرواتب (متكامل) ----------
class Employee:
    def __init__(self, name: str, emp_id: str, base_salary, allowances=0, deductions=0,
                 email: str = '', shift_type: str = 'full-time', leaves_entitled=0, leaves_used=0,
                 job_type: str = 'عامل'):
        self.name = name
        self.emp_id = emp_id
        self.email = email
        self.shift_type = shift_type
        self.job_type = job_type
        try:
            self.base_salary = Decimal(base_salary).quantize(CENT, rounding=ROUND_HALF_EVEN)
            self.allowances = Decimal(allowances).quantize(CENT, rounding=ROUND_HALF_EVEN)
            self.deductions = Decimal(deductions).quantize(CENT, rounding=ROUND_HALF_EVEN)
            self.leaves_entitled = Decimal(leaves_entitled)
            self.leaves_used = Decimal(leaves_used)
        except (InvalidOperation, TypeError):
            raise ValueError("الراتب/البدلات/الخصومات/الإجازات يجب أن تكون أرقاماً صالحة")
        if self.base_salary < 0 or self.allowances < 0 or self.deductions < 0:
            raise ValueError("القيم المالية لا يجب أن تكون سالبة")

    def absence_deduction(self) -> Decimal:
        absent_days = (self.leaves_used - self.leaves_entitled)
        if absent_days <= 0:
            return Decimal('0.00')
        daily = (self.base_salary / Decimal('30')).quantize(CENT, rounding=ROUND_HALF_EVEN)
        deduction = (daily * absent_days).quantize(CENT, rounding=ROUND_HALF_EVEN)
        return deduction

    def total_deductions(self) -> Decimal:
        total = (self.deductions + self.absence_deduction()).quantize(CENT, rounding=ROUND_HALF_EVEN)
        return total

    def net_pay(self) -> Decimal:
        net = (self.base_salary + self.allowances - self.total_deductions()).quantize(CENT, rounding=ROUND_HALF_EVEN)
        return net


def accrue_salary(employee: Employee, expense_account: Account, liability_account: Account) -> Transaction:
    net = employee.net_pay()
    if net <= Decimal('0.00'):
        raise ValueError("صافي الراتب يجب أن يكون موجباً للاقتطاع كاستحقاق")
    tx = Transaction(description=f"استحقاق راتب: {employee.emp_id} - {employee.name}")
    tx.add_entry(expense_account, 'debit', net)
    tx.add_entry(liability_account, 'credit', net)
    tx.commit()
    return tx


def pay_salary(employee: Employee, liability_account: Account, cash_account: Account) -> Transaction:
    net = employee.net_pay()
    if net <= Decimal('0.00'):
            raise ValueError("صافي الراتب يجب أن يكون موجباً لعملية الدفع")
    tx = Transaction(description=f"صرف راتب: {employee.emp_id} - {employee.name}")
    tx.add_entry(liability_account, 'debit', net)
    tx.add_entry(cash_account, 'credit', net)
    tx.commit()
    return tx


# ---------- تسوية الجرد (التوالف والناقص) ----------
def record_inventory_loss(amount, loss_account: Account, inventory_account: Account) -> Transaction:
    try:
        amt = Decimal(amount).quantize(CENT, rounding=ROUND_HALF_EVEN)
    except (InvalidOperation, TypeError):
        raise ValueError("المبلغ يجب أن يكون رقمياً صالحاً")
    if amt <= Decimal('0.00'):
        raise ValueError("مبلغ التسوية يجب أن يكون موجباً")
    tx = Transaction(description=f"تسوية جردية - توالف: {amt}")
    tx.add_entry(loss_account, 'debit', amt)
    tx.add_entry(inventory_account, 'credit', amt)
    tx.commit()
    return tx


# ---------- نظام المتجر الإلكتروني (واجهتين) ----------
def place_order(customer_account: Account, sales_account: Account, amount) -> Transaction:
    tx = Transaction(description=f"طلب متجر: {amount}")
    tx.add_entry(customer_account, 'debit', amount)
    tx.add_entry(sales_account, 'credit', amount)
    tx.commit()
    return tx


def apply_coupon(discount_account: Account, customer_account: Account, discount_amount) -> Transaction:
    tx = Transaction(description=f"كوبون خصم: {discount_amount}")
    tx.add_entry(discount_account, 'debit', discount_amount)
    tx.add_entry(customer_account, 'credit', discount_amount)
    tx.commit()
    return tx


def merchant_settlement(cash_account: Account, customer_account: Account,
                        inventory_account: Account, cogs_account: Account,
                        sale_amount, cost_amount) -> None:
    tx1 = Transaction(description=f"تحصيل دفعة وتسوية عميل: {sale_amount}")
    tx1.add_entry(cash_account, 'debit', sale_amount)
    tx1.add_entry(customer_account, 'credit', sale_amount)
    tx1.commit()

    tx2 = Transaction(description=f"تكلفة بضاعة مباعة: {cost_amount}")
    tx2.add_entry(cogs_account, 'debit', cost_amount)
    tx2.add_entry(inventory_account, 'credit', cost_amount)
    tx2.commit()


# ---------- إدارة المنتجات وواجهة المتجر ----------
def add_product(code: str, name: str, price, quantity: int):
    # price as Decimal string or number
    try:
        price_d = Decimal(price).quantize(CENT, rounding=ROUND_HALF_EVEN)
    except (InvalidOperation, TypeError):
        raise ValueError('سعر المنتج يجب أن يكون رقمياً صالحاً')
    PRODUCTS[code] = {'name': name, 'price': decimal_to_str(price_d), 'quantity': int(quantity)}
    save_all_persistence()


def renderStore() -> str:
    """محاكاة توليد HTML لواجهة العميل تعرض المنتجات"""
    html = ['<div class="store">']
    for code, p in PRODUCTS.items():
        html.append(f"<div class=\"product\" data-code=\"{code}\">{p['name']} - السعر: {p['price']} - الكمية المتبقية: {p['quantity']}</div>")
    html.append('</div>')
    return '\n'.join(html)


def buyFromStore(product_code: str, quantity: int, customer_account: Account, sales_account: Account) -> Dict:
    """عند الشراء: تحقق الكمية، أنشئ طلبًا، خصم م�� المخزون (PRODUCTS quantity)، وسجل طلب/شراء"""
    if product_code not in PRODUCTS:
        raise ValueError('المنتج غير موجود')
    if quantity <= 0:
        raise ValueError('الكمية يجب أن تكون موجبة')
    prod = PRODUCTS[product_code]
    if prod['quantity'] < quantity:
        raise ValueError('الكمية غير متوفرة في المخزون')
    # احسب السعر الكلي
    price = Decimal(prod['price'])
    total = (price * Decimal(quantity)).quantize(CENT, rounding=ROUND_HALF_EVEN)

    # أنشئ قيد مبيعات للعميل
    place_order(customer_account, sales_account, total)

    # نقص الكمية فوراً
    prod['quantity'] -= int(quantity)

    # سجل الطلب
    order = {'product': product_code, 'quantity': int(quantity), 'total': decimal_to_str(total), 'status': 'new'}
    ORDERS.append(order)
    PURCHASES.append({'product': product_code, 'quantity': int(quantity), 'amount': decimal_to_str(total)})

    # حفظ التغييرات
    save_all_persistence()

    # محاكاة تحوّل الحالة تلقائياً
    order['status'] = 'preparing'
    order['status'] = 'shipped'
    order['status'] = 'delivered'

    # بعد التسليم يمكن استدعاء تسوية البائع إن أردت (ليست مطلوبة هنا)
    save_all_persistence()
    return order


# ---------- نظام المحافظ والاستثمار (الكنز) ----------
def fund_merchant_from_investors(investor_wallet: Account, cash_account: Account, amount) -> Transaction:
    tx = Transaction(description=f"تمويل تاجر من مستثمرين: {amount}")
    tx.add_entry(cash_account, 'debit', amount)
    tx.add_entry(investor_wallet, 'credit', amount)
    tx.commit()
    FUNDINGS.append({'from': investor_wallet.code, 'to': cash_account.code, 'amount': decimal_to_str(Decimal(amount))})
    save_all_persistence()
    return tx


def purchase_inventory_financed(inventory_account: Account, supplier_account: Account, amount) -> Transaction:
    tx = Transaction(description=f"شراء مخزون ممول: {amount}")
    tx.add_entry(inventory_account, 'debit', amount)
    tx.add_entry(supplier_account, 'credit', amount)
    tx.commit()
    PURCHASES.append({'inventory': inventory_account.code, 'supplier': supplier_account.code, 'amount': decimal_to_str(Decimal(amount))})
    save_all_persistence()
    return tx


# ---------- اختبارات الوحدة الشاملة مع فحص الـ Persistence وعمليات الشراء ----------
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

    def test_products_and_buy_from_store_decrements_stock(self):
        # إعداد الحسابات والمخزون
        assets = Account("1", "الأصول", nature='debit')
        cash = Account('111', 'الصندوق', parent=assets, nature='debit')
        customer = Account('113', 'عملاء_متجر', nature='debit')
        sales = Account('411', 'مبيعات_متجر', nature='credit')
        inventory = Account('121', 'المخزون', nature='debit')

        # أضف منتجات
        add_product('P001', 'جوال', '150.00', 10)
        add_product('P002', 'ساعة', '50.00', 20)

        # تحقق من عرض الواجهة
        html = renderStore()
        self.assertIn('جوال', html)
        self.assertIn('150.00', html)

        # اشترِ 2 جوال
        order = buyFromStore('P001', 2, customer, sales)
        self.assertEqual(order['status'], 'delivered')
        # تحقق من نقص الكمية في المنتجات
        self.assertEqual(PRODUCTS['P001']['quantity'], 8)

        # تحقق من أن ملف store_db.json عكس التغيير
        with open(STORE_DB_FILE, 'r', encoding='utf-8') as f:
            sdata = json.load(f)
        prods = {p['code']: p for p in sdata.get('products', [])}
        self.assertEqual(int(prods['P001']['quantity']), 8)

    # ... بقية الاختبارات السابقة تُبقى كما هي لعدم تكرارها هنا

if __name__ == '__main__':
    # حاول تحميل قواعد بيانات سابقة إن وُجدت
    load_invest_db()
    load_store_db()
    unittest.main(verbosity=2)
