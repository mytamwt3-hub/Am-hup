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
        # نفترض أن التغير قد تم تقريبه مسبقاً عند الإنشاء أو في مكان الحساب
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
    عند التطبيق نحسب التغير الصافي لكل حساب على شكل Decimal ثم نطبقه.
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

# ---------- نظام شؤون الموظفين والرواتب (متكامل) ----------
class Employee:
    def __init__(self, name: str, emp_id: str, base_salary, allowances=0, deductions=0,
                 email: str = '', shift_type: str = 'full-time', leaves_entitled=0, leaves_used=0,
                 job_type: str = 'عامل'):
        """
        job_type: كاشير، عامل، مدير، مندوب توصيل
        leaves_entitled, leaves_used: number of leave days
        خصم الغياب يحسب عندما leaves_used > leaves_entitled
        """
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
        """إذا تجاوزت leaves_used الإجازات المستحقة، يتم خصم أيام الغياب من الراتب بشكل يومي (قاعدة: 30 يومًا للشهر)."""
        absent_days = (self.leaves_used - self.leaves_entitled)
        if absent_days <= 0:
            return Decimal('0.00')
        # حساب الأجر اليومي من خلال قسمة الراتب الأساسي على 30 ثم تقريب
        daily = (self.base_salary / Decimal('30')).quantize(CENT, rounding=ROUND_HALF_EVEN)
        deduction = (daily * absent_days).quantize(CENT, rounding=ROUND_HALF_EVEN)
        return deduction

    def total_deductions(self) -> Decimal:
        # مجموع الخصومات المدخلة زائد خصم الغياب المحسوب
        total = (self.deductions + self.absence_deduction()).quantize(CENT, rounding=ROUND_HALF_EVEN)
        return total

    def net_pay(self) -> Decimal:
        net = (self.base_salary + self.allowances - self.total_deductions()).quantize(CENT, rounding=ROUND_HALF_EVEN)
        return net


def accrue_salary(employee: Employee, expense_account: Account, liability_account: Account) -> Transaction:
    """تسجل استحقاق راتب: مدين لمصروفات الرواتب (521) ودائن لرواتب مستحقة (213) بالصافي"""
    net = employee.net_pay()
    if net <= Decimal('0.00'):
        raise ValueError("صافي الراتب يجب أن يكون موجباً للاقتطاع كاستحقاق")
    tx = Transaction(description=f"استحقاق راتب: {employee.emp_id} - {employee.name}")
    tx.add_entry(expense_account, 'debit', net)
    tx.add_entry(liability_account, 'credit', net)
    tx.commit()
    return tx


def pay_salary(employee: Employee, liability_account: Account, cash_account: Account) -> Transaction:
    """تسجل صرف راتب: مدين لرواتب مستحقة (213) ودائن للصندوق (111) عند الدفع"""
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
    """تسجيل خسارة جردية: مدين لحساب 525_بضاعة_تالفة، دائن لِـ 121_المخزون"""
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
    """واجهة العميل: تسجيل طلب على الحساب (مدين لحساب العملاء 113، دائن للمبيعات 411)"""
    tx = Transaction(description=f"طلب متجر: {amount}")
    tx.add_entry(customer_account, 'debit', amount)
    tx.add_entry(sales_account, 'credit', amount)
    tx.commit()
    return tx


def apply_coupon(discount_account: Account, customer_account: Account, discount_amount) -> Transaction:
    """تسجيل كوبون خصم: مدين لِـ 42_خصم_مسموح، دائن لِـ 113_عملاء_متجر (يقلل من مدين العملاء)"""
    tx = Transaction(description=f"كوبون خصم: {discount_amount}")
    tx.add_entry(discount_account, 'debit', discount_amount)
    tx.add_entry(customer_account, 'credit', discount_amount)
    tx.commit()
    return tx


def merchant_settlement(cash_account: Account, customer_account: Account,
                        inventory_account: Account, cogs_account: Account,
                        sale_amount, cost_amount) -> None:
    """واجهة التاجر: عند التسليم واستلام الكاش، يتم تحصيل النقد ومسح حساب العميل وتقليل المخزون (COGS vs Inventory)."""
    # تسوية الدفع من العميل
    tx1 = Transaction(description=f"تحصيل دفعة وتسوية عميل: {sale_amount}")
    tx1.add_entry(cash_account, 'debit', sale_amount)
    tx1.add_entry(customer_account, 'credit', sale_amount)
    tx1.commit()

    # تسجيل تكلفة البضاعة المباعة: مدين COGS، دائن المخزون
    tx2 = Transaction(description=f"تكلفة بضاعة مباعة: {cost_amount}")
    tx2.add_entry(cogs_account, 'debit', cost_amount)
    tx2.add_entry(inventory_account, 'credit', cost_amount)
    tx2.commit()

# ---------- نظام المحافظ والاستثمار (الكنز) ----------
def fund_merchant_from_investors(investor_wallet: Account, cash_account: Account, amount) -> Transaction:
    """دورة تمويل: تحويل من محفظة المستثمرين إلى الصندوق (تمويل للتاجر)"""
    tx = Transaction(description=f"تمويل تاجر من مستثمرين: {amount}")
    tx.add_entry(cash_account, 'debit', amount)
    tx.add_entry(investor_wallet, 'credit', amount)
    tx.commit()
    return tx


def purchase_inventory_financed(inventory_account: Account, supplier_account: Account, amount) -> Transaction:
    """شراء مخزون بتمويل: مدين للمخزون 121، دائن للموردين 211"""
    tx = Transaction(description=f"شراء مخزون ممول: {amount}")
    tx.add_entry(inventory_account, 'debit', amount)
    tx.add_entry(supplier_account, 'credit', amount)
    tx.commit()
    return tx

# ---------- اختبارات الوحدة الشاملة ----------
class TestMetaHubAccounting(unittest.TestCase):
    def test_double_entry_cash_sale(self):
        # إعداد حسابات أساسية
        assets = Account("1", "الأصول", nature='debit')
        cash = Account("111", "الصندوق", parent=assets, nature='debit')
        sales = Account("411", "المبيعات", nature='credit')

        # عملية بيع نقدي: مدين للصندوق، دائن للمبيعات
        tx = Transaction(description="بيع نقدي")
        tx.add_entry(cash, 'debit', '1500.00')
        tx.add_entry(sales, 'credit', '1500.00')
        tx.commit()

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
        tx.add_entry(cash, 'debit', '1000.01')
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

        tx = Transaction('إيداع و��بيعات')
        tx.add_entry(bank, 'debit', '500.26')
        tx.add_entry(current, 'debit', '99.75')
        tx.add_entry(revenue, 'credit', '600.01')
        tx.commit()

        self.assertEqual(bank.balance, Decimal('500.26'))
        self.assertEqual(current.balance, Decimal('600.01'))
        self.assertEqual(root.balance, Decimal('600.01'))
        self.assertEqual(revenue.balance, Decimal('600.01'))

    def test_salary_accrual_and_payment_with_leaves_and_new_accounts(self):
        # إعداد الحسابات الهرمية والضرورية للرواتب مع أرقام حسابات محدَّثة
        assets = Account("1", "الأصول", nature='debit')
        cash = Account("111", "الصندوق", parent=assets, nature='debit')

        expenses = Account('5', 'المصروفات', nature='debit')
        payroll_expense = Account('521', 'مصروفات الرواتب', parent=expenses, nature='debit')  # 521

        liabilities = Account('2', 'الخصوم', nature='credit')
        payroll_liability = Account('213', 'رواتب مستحقة', parent=liabilities, nature='credit')  # 213

        # أنشئ موظف مع إجازة مستخدمة تزيد عن المستحقة (يسبب خصم غياب)
        emp = Employee(name='أحمد', emp_id='E001', base_salary='2000.00', allowances='200.00',
                       deductions='150.00', leaves_entitled=2, leaves_used=4, email='a@example.com', job_type='كاشير')
        absence_ded = emp.absence_deduction()
        self.assertEqual(absence_ded, Decimal('133.34'))

        net = emp.net_pay()
        self.assertEqual(net, Decimal('1916.66'))

        # استحقاق الراتب (قيد): مدين 521، دائن 213
        accrue_tx = accrue_salary(emp, payroll_expense, payroll_liability)
        self.assertEqual(payroll_expense.balance, net)
        self.assertEqual(expenses.balance, net)
        self.assertEqual(payroll_liability.balance, net)

        # صرف الراتب (قيد): مدين 213، دائن 111
        pay_tx = pay_salary(emp, payroll_liability, cash)
        self.assertEqual(payroll_liability.balance, Decimal('0.00'))
        self.assertEqual(cash.balance, -net)

    def test_inventory_loss_recording(self):
        # إعداد الحسابات
        expenses = Account('5', 'المصروفات', nature='debit')
        loss_account = Account('525', 'بضاعة تالفة', parent=expenses, nature='debit')
        inventory = Account('121', 'المخزون', nature='debit')

        # ضع رصيد مبدئي للمخزون
        inventory.balance = Decimal('1000.00')

        # سجّل خسارة جردية
        tx = record_inventory_loss('50.25', loss_account, inventory)

        # التوقعات: زيادة مصروف البضاعة التالفة ونقصان المخزون
        self.assertEqual(loss_account.balance, Decimal('50.25'))
        self.assertEqual(expenses.balance, Decimal('50.25'))
        self.assertEqual(inventory.balance, Decimal('949.75'))

    def test_store_sale_distribution_to_wallets(self):
        # إعداد الحسابات: الصندوق (111)، محافظ المستثمرين/التجار/المنصة
        assets = Account("1", "الأصول", nature='debit')
        cash = Account('111', 'الصندوق', parent=assets, nature='debit')

        # لنماذج المحافظ والعمولة: نجعلها طبيعياً دائن بحيث تزيد بالـ credit
        investor_wallet = Account('115', 'محفظة المستثمرين', nature='credit')
        merchant_wallet = Account('116', 'محفظة التجار', nature='credit')
        platform_commission = Account('417', 'عمولة_المنصة', nature='credit')

        # رصيد مبدئي للمستثمر
        investor_wallet.balance = Decimal('1000.00')

        # عملية ب��ع جوال بسعر 150 يتم توزيعها كالتالي: 115 +=130, 116 +=15, 417 +=5
        sale_amount = Decimal('150.00')
        investor_share = Decimal('130.00')
        merchant_share = Decimal('15.00')
        platform_share = Decimal('5.00')

        # نُنشئ قيدًا مركبًا واحدًا متوازنًا
        tx = Transaction(description='بيع متجر - توزيع أرباح')
        tx.add_entry(cash, 'debit', sale_amount)
        tx.add_entry(investor_wallet, 'credit', investor_share)
        tx.add_entry(merchant_wallet, 'credit', merchant_share)
        tx.add_entry(platform_commission, 'credit', platform_share)
        # يجب أن يكون متوازنًا
        tx.commit()

        # تحقّق من رصيد المستثمر ازداد من 1000 إلى 1130
        self.assertEqual(investor_wallet.balance, Decimal('1130.00'))
        # تحقق توازن: مجموع الدائن = مجموع المدين (ضمن التنفيذ لم يتم رفع ValueError)
        self.assertEqual(cash.balance, sale_amount)
        self.assertEqual(merchant_wallet.balance, Decimal('15.00'))
        self.assertEqual(platform_commission.balance, Decimal('5.00'))

if __name__ == '__main__':
    unittest.main(verbosity=2)
