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
        'purchases': PURCHASES
    }
    with open(STORE_DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def save_all_persistence():
    # Ensure directory exists (repo root)
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


class Account:
    def __init__(self, code: str, name: str, parent: 'Account' = None, nature: str = 'debit'):
        if nature not in ('debit', 'credit'):
            raise ValueError("الطبيعة يجب أن تكون 'debit' (مدين) أو 'credit' (دائن)")
        self.code = code
        self.name = name
        self.parent = parent
        self.nature = nature
        self.balance = Decimal('0.00')
        # سجل تلقائي
        ACCOUNTS[self.code] = self

    def _apply_change(self, delta: Decimal):
        if not isinstance(delta, Decimal):
            raise TypeError("delta يجب أن يكون من نوع Decimal")
        # تطبيق التغير
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

        # بعد تطبيق التغيرات احفظ الحالة تلقائياً
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


# ---------- نظام المحافظ والاستثمار (الكنز) ----------
def fund_merchant_from_investors(investor_wallet: Account, cash_account: Account, amount) -> Transaction:
    tx = Transaction(description=f"تمويل تاجر من مستثمرين: {amount}")
    tx.add_entry(cash_account, 'debit', amount)
    tx.add_entry(investor_wallet, 'credit', amount)
    tx.commit()
    # سجل التمويل
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


# ---------- اختبارات الوحدة الشاملة مع فحص الـ Persistence ----------
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

    def test_salary_accrual_and_payment_with_leaves_and_new_accounts(self):
        assets = Account("1", "الأصول", nature='debit')
        cash = Account("111", "الصندوق", parent=assets, nature='debit')

        expenses = Account('5', 'المصروفات', nature='debit')
        payroll_expense = Account('521', 'مصروفات الرواتب', parent=expenses, nature='debit')

        liabilities = Account('2', 'الخصوم', nature='credit')
        payroll_liability = Account('213', 'رواتب مستحقة', parent=liabilities, nature='credit')

        emp = Employee(name='أحمد', emp_id='E001', base_salary='2000.00', allowances='200.00',
                       deductions='150.00', leaves_entitled=2, leaves_used=4, email='a@example.com', job_type='كاشير')
        absence_ded = emp.absence_deduction()
        self.assertEqual(absence_ded, Decimal('133.34'))

        net = emp.net_pay()
        self.assertEqual(net, Decimal('1916.66'))

        accrue_tx = accrue_salary(emp, payroll_expense, payroll_liability)
        self.assertEqual(payroll_expense.balance, net)
        self.assertEqual(expenses.balance, net)
        self.assertEqual(payroll_liability.balance, net)

        pay_tx = pay_salary(emp, payroll_liability, cash)
        self.assertEqual(payroll_liability.balance, Decimal('0.00'))
        self.assertEqual(cash.balance, -net)

    def test_inventory_loss_recording(self):
        expenses = Account('5', 'المصروفات', nature='debit')
        loss_account = Account('525', 'بضاعة تالفة', parent=expenses, nature='debit')
        inventory = Account('121', 'المخزون', nature='debit')

        inventory.balance = Decimal('1000.00')

        tx = record_inventory_loss('50.25', loss_account, inventory)

        self.assertEqual(loss_account.balance, Decimal('50.25'))
        self.assertEqual(expenses.balance, Decimal('50.25'))
        self.assertEqual(inventory.balance, Decimal('949.75'))

    def test_store_sale_distribution_to_wallets_and_persistence(self):
        assets = Account("1", "الأصول", nature='debit')
        cash = Account('111', 'الصندوق', parent=assets, nature='debit')

        investor_wallet = Account('115', 'محفظة المستثمرين', nature='credit')
        merchant_wallet = Account('116', 'محفظة التجار', nature='credit')
        platform_commission = Account('417', 'عمولة_المنصة', nature='credit')

        investor_wallet.balance = Decimal('1000.00')

        sale_amount = Decimal('150.00')
        investor_share = Decimal('130.00')
        merchant_share = Decimal('15.00')
        platform_share = Decimal('5.00')

        tx = Transaction(description='بيع متجر - توزيع أرباح')
        tx.add_entry(cash, 'debit', sale_amount)
        tx.add_entry(investor_wallet, 'credit', investor_share)
        tx.add_entry(merchant_wallet, 'credit', merchant_share)
        tx.add_entry(platform_commission, 'credit', platform_share)
        tx.commit()

        self.assertEqual(investor_wallet.balance, Decimal('1130.00'))
        self.assertEqual(cash.balance, sale_amount)
        self.assertEqual(merchant_wallet.balance, Decimal('15.00'))
        self.assertEqual(platform_commission.balance, Decimal('5.00'))

        # تحقق من أن البيانات دُفعت إلى invest_db.json
        with open(INVEST_DB_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        wallets = {w['code']: Decimal(w['balance']) for w in data.get('wallets', [])}
        self.assertEqual(wallets.get('115'), Decimal('1130.00'))

    def test_persistence_on_funding_and_purchase(self):
        # تمويل من محفظة المستثمرين إلى الصندوق
        assets = Account("1", "الأصول", nature='debit')
        cash = Account('111', 'الصندوق', parent=assets, nature='debit')
        investor_wallet = Account('115', 'محفظة المستثمرين', nature='credit')
        investor_wallet.balance = Decimal('500.00')

        fund_merchant_from_investors(investor_wallet, cash, '200.00')
        # بعد التمويل يجب تحديث FUNDINGS وملف invest_db.json
        with open(INVEST_DB_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        # تأكد من وجود سجل التمويل
        self.assertTrue(any(item['from'] == '115' and item['to'] == '111' and Decimal(item['amount']) == Decimal('200.00') for item in data.get('fundings', [])))

        # شراء مخزون ممول
        supplier = Account('211', 'الموردين', nature='credit')
        inventory = Account('121', 'المخزون', nature='debit')
        purchase_inventory_financed(inventory, supplier, '300.50')
        with open(STORE_DB_FILE, 'r', encoding='utf-8') as f:
            sdata = json.load(f)
        self.assertTrue(any(p['inventory'] == '121' and Decimal(p['amount']) == Decimal('300.50') for p in sdata.get('purchases', [])))

if __name__ == '__main__':
    # حاول تحميل قواعد بيانات سابقة إن وُجدت
    load_invest_db()
    load_store_db()
    unittest.main(verbosity=2)
