# ملف: test_accounting.py
import unittest

# استدعاء كود الحسابات الرئيسي من ملفك الأول
from chart_of_accounts import Account

class TestMetaHubSystem(unittest.TestCase):
    def test_hierarchical_accounting_flow(self):
        """فحص حركة القيود الهرمية لمشروع ميتا هوب"""
        
        # 1. بناء شجرة الحسابات الهرمية بناءً على صورتك
        assets = Account("1", "الأصول")
        cash = Account("111", "الصندوق", parent=assets)
        inventory = Account("121", "المخزون", parent=assets)
        
        revenues = Account("4", "الإيرادات")
        sales = Account("411", "المبيعات", parent=revenues)

        # 2. محاكاة [فاتورة بيع نقداً] بقيمة 1500 ريال
        # القيد المحاسبي: من 111 الصندوق (يزيد) إلى 411 المبيعات (تزيد)
        invoice_amount = 1500.0
        cash.update_balance(invoice_amount)
        sales.update_balance(invoice_amount)

        # 3. الفحص التلقائي لنتائج المبيعات والصندوق والأصول
        self.assertEqual(cash.balance, 1500.0)      # فحص رصيد الصندوق الحقيقي
        self.assertEqual(sales.balance, 1500.0)     # فحص رصيد المبيعات الحقيقي
        self.assertEqual(assets.balance, 1500.0)    # فحص الأصول (هل زادت هرمياً تلقائياً؟)

        # 4. محاكاة [فاتورة شراء نقداً] للمخزون بقيمة 500 ريال
        # القيد: من 121 المخزون (يزيد) إلى 111 الصندوق (ينقص)
        purchase_amount = 500.0
        inventory.update_balance(purchase_amount)
        cash.update_balance(-purchase_amount) # سحب الكاش من الصندوق

        # 5. الفحص التلقائي بعد الشراء وتحديث المخزون اللحظي
        self.assertEqual(inventory.balance, 500.0)  # فحص رصيد المخزون اللحظي
        self.assertEqual(cash.balance, 1000.0)       # الصندوق يجب أن ينقص (1500 - 500 = 1000)
        self.assertEqual(assets.balance, 1500.0)    # إجمالي الأصول يجب أن يبقى ثابتاً وتوازناً

        print("\n\n✅ نجح الفحص! شجرة الحسابات تتوازن هرمياً وتحديث المخزون اللحظي يعمل بدون أخطاء.")

if __name__ == '__main__':
    unittest.main()
