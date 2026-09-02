import unittest
from decimal import Decimal, InvalidOperation, getcontext
from typing import Dict

# ضبط دقة عشرية مناسبة (النتائج ستكون دقيقة؛ سنستخدم quantize عند الحاجة لتقليل الكسور)
getcontext().prec = 28

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
        # استخدام تنسيق ثابت إن رغبت: amt = amt.quantize(Decimal('0.01'))
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

        # طبق التغيرات (تطبيق واحد لكل ح��اب، وPropagation داخل _apply_change)
        for account, delta in net_changes.items():
            account._apply_change(delta)

class TestMetaHubAccounting(unittest.TestCase):
    def test_double_entry_cash_sale(self):
        # إعداد الحسابات
        assets = Account("1", "الأصول", nature='debit')
        cash = Account("111", "الصندوق", parent=assets, nature='debit')
        sales = Account("411", "المبيعات", nature='credit')

        # عملية بيع نقدي: مدين للصندوق، دائن للمبيعات
        tx = Transaction(description="بيع نقدي")
        tx.add_entry(cash, 'debit', '1500.00')
        tx.add_entry(sales, 'credit', '1500.00')
        tx.commit()

        # توقعات: زيادة في الصندوق (+1500)، هذا ينعكس في الأصل (+1500)
        self.assertEqual(cash.balance, Decimal('1500.00'))
        self.assertEqual(assets.balance, Decimal('1500.00'))
        # المبيعات طبيعتها دائنة فتزداد بقيمة 1500
        self.assertEqual(sales.balance, Decimal('1500.00'))

    def test_reject_unbalanced_transaction_and_no_side_effects(self):
        assets = Account("1", "الأصول", nature='debit')
        cash = Account("111", "الصندوق", parent=assets, nature='debit')
        sales = Account("411", "المبيعات", nature='credit')

        # تذكر الأرصدة قبل المحاولة
        before_cash = cash.balance
        before_assets = assets.balance
        before_sales = sales.balance

        tx = Transaction(description="معاملة غير متزنة")
        tx.add_entry(cash, 'debit', '1000.00')
        tx.add_entry(sales, 'credit', '900.00')

        with self.assertRaises(ValueError):
            tx.commit()

        # تأكد أن الأرصدة لم تتغير بعد فشل الحفظ
        self.assertEqual(cash.balance, before_cash)
        self.assertEqual(assets.balance, before_assets)
        self.assertEqual(sales.balance, before_sales)

    def test_multiple_entries_and_hierarchy(self):
        # اختبار مع أطراف متعددة لنفس الحساب وتدرج هرمي
        root = Account('0', 'الميزان', nature='debit')
        current = Account('11', 'الحالي', parent=root, nature='debit')
        bank = Account('112', 'البنك', parent=current, nature='debit')
        revenue = Account('411', 'المبيعات', nature='credit')

        tx = Transaction('إيداع ومبيعات')
        tx.add_entry(bank, 'debit', '500.25')
        tx.add_entry(current, 'debit', '99.75')
        tx.add_entry(revenue, 'credit', '600.00')
        tx.commit()

        self.assertEqual(bank.balance, Decimal('500.25'))
        self.assertEqual(current.balance, Decimal('600.00'))  # 500.25 + 99.75
        self.assertEqual(root.balance, Decimal('600.00'))
        self.assertEqual(revenue.balance, Decimal('600.00'))

if __name__ == '__main__':
    unittest.main(verbosity=2)
