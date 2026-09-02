import unittest
from typing import Dict

class Account:
    """
    account.nature: either 'debit' (طبيعة مدينة) or 'credit' (طبيعة دائنة)
    balance: positive number representing the account's normal balance
    """
    def __init__(self, code: str, name: str, parent: 'Account' = None, nature: str = 'debit'):
        if nature not in ('debit', 'credit'):
            raise ValueError("nature must be 'debit' or 'credit'")
        self.code = code
        self.name = name
        self.parent = parent
        self.nature = nature
        self.balance = 0.0

    def _apply_change(self, delta: float):
        """
        Apply a signed change to this account and propagate the same signed change
        to parent accounts (hierarchical roll-up).
        delta > 0 means increase the account's balance.
        delta < 0 means decrease the account's balance.
        """
        self.balance += delta
        if self.parent:
            self.parent._apply_change(delta)

class Entry:
    """
    A single side of a transaction: debit or credit to an account with an amount (positive).
    """
    def __init__(self, account: Account, side: str, amount: float):
        if side not in ('debit', 'credit'):
            raise ValueError("side must be 'debit' or 'credit'")
        if amount <= 0:
            raise ValueError("amount must be positive")
        self.account = account
        self.side = side
        self.amount = float(amount)

class Transaction:
    """
    Holds entries and enforces Debits == Credits on commit.
    When committing, computes net signed changes per account and applies them atomically.
    """
    def __init__(self, description: str = ""):
        self.description = description
        self.entries = []

    def add_entry(self, account: Account, side: str, amount: float):
        self.entries.append(Entry(account, side, amount))

    def commit(self):
        if not self.entries:
            raise ValueError("Transaction has no entries")

        total_debits = sum(e.amount for e in self.entries if e.side == 'debit')
        total_credits = sum(e.amount for e in self.entries if e.side == 'credit')

        # شرط الفحص الصارم: يجب أن يكون المجموعان متطابقين تماماً
        if total_debits != total_credits:
            raise ValueError(f"Transaction not balanced: Debits={total_debits} != Credits={total_credits}")

        # احسب التغير الصافي لكل حساب (مجموع التأثيرات الموقعة)
        net_changes: Dict[Account, float] = {}
        for e in self.entries:
            # إذا كانت طبيعة الحساب تطابق الجانب، فالتأثير موجب (زيادة)
            if e.side == e.account.nature:
                signed = e.amount
            else:
                signed = -e.amount

            net_changes[e.account] = net_changes.get(e.account, 0.0) + signed

        # طبق التغيرات (تطبيق واحد لكل حساب، وPropagation داخل _apply_change)
        for account, delta in net_changes.items():
            account._apply_change(delta)

class TestMetaHubAccounting(unittest.TestCase):
    def test_double_entry_cash_sale(self):
        # حسابات: الأصل مدين، الصندوق مدين، المبيعات دائنة
        assets = Account("1", "الأصول", nature='debit')
        cash = Account("111", "الصندوق", parent=assets, nature='debit')
        sales = Account("411", "المبيعات", nature='credit')

        # عملية بيع نقدي: مدين للصندوق، دائن للمبيعات
        tx = Transaction(description="بيع نقدي")
        tx.add_entry(cash, 'debit', 1500.0)
        tx.add_entry(sales, 'credit', 1500.0)
        tx.commit()

        # توقعات: زيادة في الصندوق (+1500)، هذا ينعكس في الأصل (+1500)
        self.assertEqual(cash.balance, 1500.0)
        self.assertEqual(assets.balance, 1500.0)
        # المبيعات طبيعتها دائنة فتزداد بقيمة 1500
        self.assertEqual(sales.balance, 1500.0)

    def test_reject_unbalanced_transaction_and_no_side_effects(self):
        assets = Account("1", "الأصول", nature='debit')
        cash = Account("111", "الصندوق", parent=assets, nature='debit')
        sales = Account("411", "المبيعات", nature='credit')

        # تذكر الأرصدة قبل المحاولة
        before_cash = cash.balance
        before_assets = assets.balance
        before_sales = sales.balance

        tx = Transaction(description="معاملة غير متزنة")
        tx.add_entry(cash, 'debit', 1000.0)
        tx.add_entry(sales, 'credit', 900.0)

        with self.assertRaises(ValueError):
            tx.commit()

        # تأكد أن الأرصدة لم تتغير بعد فشل الحفظ
        self.assertEqual(cash.balance, before_cash)
        self.assertEqual(assets.balance, before_assets)
        self.assertEqual(sales.balance, before_sales)

if __name__ == '__main__':
    unittest.main(verbosity=2)
