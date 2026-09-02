import unittest
from decimal import Decimal, InvalidOperation, getcontext, ROUND_HALF_EVEN
from typing import Dict

# ضبط دقة عشرية مناسبة والـ rounding الافتراضي
getcontext().prec = 28
getcontext().rounding = ROUND_HALF_EVEN

CENT = Decimal('0.01')

class Account:
    def __init__(self, code: str, name: str, parent: 'Account' = None, nature: str = 'debit'):
        if nature not in ('debit', 'credit'):
            raise ValueError("الطبيعة يجب أن تكون 'debit' (مدين) أو 'credit' (دائن)")
        self.code = code
        self.name = name
        self.parent = parent
        self.nature = nature
        self.balance = Decimal('0.00')

    def _apply_change(self, delta: Decimal):
        if not isinstance(delta, Decimal):
            raise TypeError("delta يجب أن يكون من نوع Decimal")
        # نفترض أن التغير قد تم تقريبه مسبقاً عند الإنشاء
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
        # تقريــب تلقائي إلى منزلتين عشريتين (الهللة/القرش)
        amt = amt.quantize(CENT, rounding=ROUND_HALF_EVEN)
        self.account = account
        self.side = side
        self.amount = amt

    def __repr__(self):
        return f"Entry(account={self.account.code!r}, side={self.side!r}, amount={self.amount})"

class Transaction:
    """
    تمثل قيد محاسبي متعدد الأسطر. قبل التطبيق نتحقق أن مجموع المدين = مجموع الدائن.
    عند التطبيق نحسب التغير ��لصافي لكل حساب على شكل Decimal ثم نطبقه.
    """
    def __init__(self, description: str = ""):
        self.description = description
        self.entries = []

    def add_entry(self, account: Account, side: str, amount):
        # Entry سيقوم بالتقريب عند الإنشاء
        self.entries.append(Entry(account, side, amount))

    def commit(self):
        if not self.entries:
            raise ValueError("التسجيلة لا تحتوي على أطراف")

        total_debits = sum((e.amount for e in self.entries if e.side == 'debit'), Decimal('0.00'))
        total_credits = sum((e.amount for e in self.entries if e.side == 'credit'), Decimal('0.00'))

        # شرط الفحص الصارم: يجب أن يكون المجموعان متطابقين تماماً
        if total_debits != total_credits:
            raise ValueError(f"المعاملة غير متزنة: المدين={total_debits} != الدائن={total_credits}")

        # احسب التغير الصافي لكل حساب (مجموع التأثيرات الموقعة)
        net_changes: Dict[Account, Decimal] = {}
        for e in self.entries:
            # إذا كانت طبيعة الحساب تطابق الجانب، فالتأثير موجب (زيادة)
            signed = e.amount if e.side == e.account.nature else -e.amount
            net_changes[e.account] = net_changes.get(e.account, Decimal('0.00')) + signed

        # طبق التغيرات (تطبيق واحد لكل حساب، وPropagation داخل _apply_change)
        for account, delta in net_changes.items():
            account._apply_change(delta)

# ---------- نظام شؤون الموظفين والرواتب ----------
class Employee:
    def __init__(self, name: str, emp_id: str, base_salary, allowances=0, deductions=0):
        self.name = name
        self.emp_id = emp_id
        try:
            self.base_salary = Decimal(base_salary).quantize(CENT, rounding=ROUND_HALF_EVEN)
            self.allowances = Decimal(allowances).quantize(CENT, rounding=ROUND_HALF_EVEN)
            self.deductions = Decimal(deductions).quantize(CENT, rounding=ROUND_HALF_EVEN)
        except (InvalidOperation, TypeError):
            raise ValueError("الراتب/البدلات/الخصومات يجب أن تكون أرقاماً صالحة")
        if self.base_salary < 0 or self.allowances < 0 or self.deductions < 0:
            raise ValueError("القيم المالية لا يجب أن تكون سالبة")

    def net_pay(self) -> Decimal:
        return (self.base_salary + self.allowances - self.deductions).quantize(CENT, rounding=ROUND_HALF_EVEN)

def accrue_salary(employee: Employee, expense_account: Account, liability_account: Account) -> Transaction:
    """تسجل استحقاق راتب: مدين لمصروفات الرواتب (511) ودائن لرواتب مستحقة (221) بالصافي"""
    net = employee.net_pay()
    if net <= Decimal('0.00'):
        raise ValueError("صافي الراتب يجب أن يكون موجباً للاقتطاع كاستحقاق")
    tx = Transaction(description=f"استحقاق راتب: {employee.emp_id} - {employee.name}")
    tx.add_entry(expense_account, 'debit', net)
    tx.add_entry(liability_account, 'credit', net)
    tx.commit()
    return tx

def pay_salary(employee: Employee, liability_account: Account, cash_account: Account) -> Transaction:
    """تسجل صرف راتب: مدين لرواتب مستحقة (221) ودائن للصندوق (111) عند الدفع"""
    net = employee.net_pay()
    if net <= Decimal('0.00'):
        raise ValueError("صافي الراتب يجب أن يكون موجباً لعملية الدفع")
    tx = Transaction(description=f"صرف راتب: {employee.emp_id} - {employee.name}")
    tx.add_entry(liability_account, 'debit', net)
    tx.add_entry(cash_account, 'credit', net)
    tx.commit()
    return tx

# ---------- اختبارات الوحدة ----------
class TestMetaHubAccounting(unittest.TestCase):
    def test_double_entry_cash_sale(self):
        # إعداد الحسابات
        assets = Account("1", "الأصول", nature='debit')
        cash = Account("111", "الصندوق", parent=assets, nature='debit')
        sales = Account("411", "المبيعات", nature='credit')

        # عملية بيع نقدي: مدين للصندوق، دائن للمبيعات
        tx = Transaction(description="بيع نقدي")
        tx.add_entry(cash, 'debit', '1500.004')  # سيتقرب إلى 1500.00
        tx.add_entry(sales, 'credit', '1500.004')
        tx.commit()

        # توقعات: زيادة في الصندوق (+1500.00)، هذا ينعكس في الأصل (+1500.00)
        self.assertEqual(cash.balance, Decimal('1500.00'))
        self.assertEqual(assets.balance, Decimal('1500.00'))
        self.assertEqual(sales.balance, Decimal('1500.00'))

    def test_reject_unbalanced_transaction_and_no_side_effects(self):
        assets = Account("1", "الأصول", nature='debit')
        cash = Account("111", "الصندوق", parent=assets, nature='debit')
        sales = Account("411", "المبيعات", nature='credit')

        before_cash = cash.balance
        before_assets = assets.balance
        before_sales = sales.balance

        tx = Transaction(description="معاملة غير متزنة")
        tx.add_entry(cash, 'debit', '1000.005')  # يقرب إلى 1000.01
        tx.add_entry(sales, 'credit', '900.00')

        with self.assertRaises(ValueError):
            tx.commit()

        self.assertEqual(cash.balance, before_cash)
        self.assertEqual(assets.balance, before_assets)
        self.assertEqual(sales.balance, before_sales)

    def test_multiple_entries_and_hierarchy(self):
        root = Account('0', 'الميزان', nature='debit')
        current = Account('11', 'الحالي', parent=root, nature='debit')
        bank = Account('112', 'البنك', parent=current, nature='debit')
        revenue = Account('411', 'المبيعات', nature='credit')

        tx = Transaction('إيداع ومبيعات')
        tx.add_entry(bank, 'debit', '500.255')  # يقرب إلى 500.26
        tx.add_entry(current, 'debit', '99.745')  # يقرب إلى 99.75
        tx.add_entry(revenue, 'credit', '600.005')  # يقرب إ��ى 600.01
        tx.commit()

        self.assertEqual(bank.balance, Decimal('500.26'))
        self.assertEqual(current.balance, Decimal('600.01'))  # 500.26 + 99.75
        self.assertEqual(root.balance, Decimal('600.01'))
        self.assertEqual(revenue.balance, Decimal('600.01'))

    def test_salary_accrual_and_payment(self):
        # إعداد الحسابات الهرمية والضرورية للرواتب
        assets = Account("1", "الأصول", nature='debit')
        cash = Account("111", "الصندوق", parent=assets, nature='debit')

        expenses = Account('5', 'المصروفات', nature='debit')
        payroll_expense = Account('511', 'مصروفات الرواتب', parent=expenses, nature='debit')

        liabilities = Account('2', 'الخصوم', nature='credit')
        payroll_liability = Account('221', 'رواتب مستحقة', parent=liabilities, nature='credit')

        # أنشئ موظف
        emp = Employee(name='أحمد', emp_id='E001', base_salary='2000.005', allowances='200.004', deductions='150')
        net = emp.net_pay()
        # تحقق من حساب صافي الراتب بدقة وبالتقريب إلى سنتين
        self.assertEqual(net, Decimal('2050.01'))  # 2000.01 + 200.00 - 150.00 = 2050.01

        # ��ستحقاق الراتب (قيد): مدين 511، دائن 221
        accrue_tx = accrue_salary(emp, payroll_expense, payroll_liability)
        # بعد الاستحقاق: مصروفات الرواتب وزيادة في الخصوم
        self.assertEqual(payroll_expense.balance, net)
        self.assertEqual(expenses.balance, net)
        self.assertEqual(payroll_liability.balance, net)

        # صرف الراتب (قيد): مدين 221 (يقلل الخصوم)، دائن 111 (ينقص النقد)
        pay_tx = pay_salary(emp, payroll_liability, cash)
        # بعد الصرف: الخصوم تعود للصفر، والصندوق نقص
        self.assertEqual(payroll_liability.balance, Decimal('0.00'))
        self.assertEqual(cash.balance, -net)  # since cash was credited (انخفاض في الرصيد المدين)

if __name__ == '__main__':
    unittest.main(verbosity=2)
