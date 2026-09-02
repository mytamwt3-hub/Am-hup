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

# ---------- نظام شؤون الموظفين والرواتب (محدَّث) ----------
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
    """دورة تمويل: تحويل من محفظة المستثمرين إلى الصندوق (تمويل للتاجر)
    ملاحظة: اتجاه الدفاتر يعتمد على طبيعة الحسابات؛ هنا نفترض أن wallet accounts طبيعتها 'credit' (زيادة عند credit)
    ونريد أن تنعكس الأموال في الصندوق (111) بزيادة في الجانب المدين.
    سنقوم بإنشاء قيد يَدين الصندوق ويُقِر المستثمرين (أي يخفض رصيد المحفظة إذا كانت مدين-طبيعة)،
    لكن لاعتماد ثابت نستخدم المدخل الذي يطابق متطلباتك: نَدَيْنُ الصندوق ونقرضُ المحفظة.
    """
    # سنفترض investor_wallet.nature == 'credit' (زيادة عند قيد credit)
    tx = Transaction(description=f"تمويل تاجر من مستثمرين: {amount}")
    tx.add_entry(cash_account, 'debit', amount)
    # لتقليل رصيد المحفظة (أخذ أموال منها)، نضع قيدًا دائنًا لها إذا كانت طبيعتها 'credit' يزيد بها
    # المستخدم طلب سابقًا تسجيل: من 115 (مدين) إلى 111 (دائن) - لكن للمطابقة العملية سننفّذ: credit على investor_wallet
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

# ---------- اختبار دورة بيع موزَّع الأرباح والمحافظ ----------
class TestMetaHubAccounting(unittest.TestCase):
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

        # عملية بيع جوال بسعر 150 يتم توزيعها كالتالي: 115 +=130, 116 +=15, 417 +=5
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
