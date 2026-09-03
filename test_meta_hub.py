"""
test_meta_hub.py
اختبارات الوحدة الشاملة لـ MetaHOP
"""

import unittest
import os
from decimal import Decimal
from accounting_core import (
    ACCOUNTS, PRODUCTS, ORDERS, ATTENDANCE_LOGS, CHAT_MESSAGE_LOGS,
    WHATSAPP_NOTIFICATIONS, CCTV_INVOICE_LOGS, CLOSED_REVENUES,
    Account, Employee, Merchant, Transaction, add_product,
    buyFromStore, record_attendance_biometric, send_in_app_message,
    send_whatsapp_notification, pay_salary, execute_financial_closing,
    ai_parse_and_record_invoice, ai_generate_financial_summary,
    admin_search_cctv_by_invoice,
    INVEST_DB_FILE, STORE_DB_FILE, load_store_db, load_invest_db, save_all_persistence
)


class TestMetaHubAccounting(unittest.TestCase):
    
    def setUp(self):
        # حذف ملفات التخزين
        for fname in (INVEST_DB_FILE, STORE_DB_FILE):
            try:
                os.remove(fname)
            except OSError:
                pass
        
        # مسح السجلات
        ACCOUNTS.clear()
        PRODUCTS.clear()
        ORDERS.clear()
        ATTENDANCE_LOGS.clear()
        CHAT_MESSAGE_LOGS.clear()
        WHATSAPP_NOTIFICATIONS.clear()
        CCTV_INVOICE_LOGS.clear()
        CLOSED_REVENUES.clear()
        
        # إنشاء حسابات أساسية
        assets = Account('1', 'الأصول', nature='debit')
        self.cash = Account('111', 'الصندوق', parent=assets, nature='debit')
        self.sales = Account('411', 'مبيعات_متجر', nature='credit')
        self.platform = Account('417', 'عمولة_المنصة', nature='credit')
        self.inventory_account = Account('121', 'المخزن_اللحظي', nature='debit')
        self.distribution_expense = Account('599', 'مصاريف_توزيع', nature='debit', is_temporary=True)
        
        # إضافة منتجات
        add_product('P001', 'جوال', '150.00', 10)
        add_product('P002', 'ساعة', '50.00', 20)

    def test_buy_reduces_product_and_inventory(self):
        """اختبار تقليل المنتج والمخزون عند الشراء"""
        customer = Account('113', 'عملاء_متجر', nature='debit')
        order = buyFromStore('P001', 2, customer, self.sales)
        
        self.assertEqual(PRODUCTS['P001']['quantity'], 8)
        self.assertEqual(order['invoice_id'], 'INV000001')
        self.assertTrue(len(ORDERS) > 0)

    def test_biometric_attendance_late_deduction(self):
        """اختبار حساب خصم التأخير بدقة"""
        employee = Employee('E001', 'أحمد محمد', '3000.00', '+966501234567')
        
        att_record = record_attendance_biometric(
            emp_id='E001',
            employee=employee,
            movement_type='check_in',
            time_str='09:30',
            date_str='2026-09-03'
        )
        
        self.assertTrue(att_record['is_late'])
        self.assertEqual(Decimal(att_record['deduction_amount']), Decimal('6.25'))
        self.assertEqual(employee.deductions, Decimal('6.25'))

    def test_biometric_attendance_on_time_no_deduction(self):
        """اختبار عدم وجود خصم عند الدخول في الوقت"""
        employee = Employee('E002', 'فاطمة علي', '2500.00', '+966501234568')
        
        att_record = record_attendance_biometric(
            emp_id='E002',
            employee=employee,
            movement_type='check_in',
            time_str='09:00',
            date_str='2026-09-03'
        )
        
        self.assertFalse(att_record['is_late'])
        self.assertEqual(att_record['deduction_amount'], '0.00')
        self.assertEqual(employee.deductions, Decimal('0.00'))

    def test_whatsapp_notification_on_sale(self):
        """اختبار إرسال إشعار واتساب عند البيع"""
        customer = Account('113', 'عملاء_متجر', nature='debit')
        order = buyFromStore(
            'P001', 1, customer, self.sales,
            customer_phone='+966501111111'
        )
        
        sale_notifications = [n for n in WHATSAPP_NOTIFICATIONS if n['transaction_type'] == 'sale']
        self.assertEqual(len(sale_notifications), 1)
        self.assertEqual(sale_notifications[0]['status'], 'Sent')
        self.assertIn(order['invoice_id'], sale_notifications[0]['message_text'])

    def test_whatsapp_notification_on_salary(self):
        """اختبار إرسال إشعار واتساب عند صرف الراتب"""
        employee = Employee('E001', 'أحمد محمد', '3000.00', '+966502222222')
        employee.deductions = Decimal('6.25')
        
        salary_record = pay_salary(employee, '2993.75')
        
        salary_notifications = [n for n in WHATSAPP_NOTIFICATIONS if n['transaction_type'] == 'salary']
        self.assertEqual(len(salary_notifications), 1)
        self.assertEqual(salary_notifications[0]['status'], 'Sent')

    def test_in_app_messaging(self):
        """اختبار نظام المراسلة الفورية"""
        message = send_in_app_message('user001', 'user002', 'مرحبا')
        
        self.assertEqual(message['sender'], 'user001')
        self.assertEqual(message['receiver'], 'user002')
        self.assertEqual(message['status'], 'delivered')
        self.assertEqual(len(CHAT_MESSAGE_LOGS), 1)

    def test_cctv_invoice_sync(self):
        """اختبار مزامنة الكاميرا مع الفواتير"""
        customer = Account('113', 'عملاء_متجر', nature='debit')
        order = buyFromStore('P001', 1, customer, self.sales)
        
        cctv_logs = [e for e in CCTV_INVOICE_LOGS if e['invoice_id'] == order['invoice_id']]
        self.assertEqual(len(cctv_logs), 1)
        self.assertIn('date', cctv_logs[0])
        self.assertIn('time', cctv_logs[0])
        self.assertIn('video_ref', cctv_logs[0])

    def test_admin_search_cctv(self):
        """اختبار بحث الإدمن في الكاميرات"""
        customer = Account('113', 'عملاء_متجر', nature='debit')
        order = buyFromStore('P001', 1, customer, self.sales)
        invoice_id = order['invoice_id']
        
        admin = Merchant('A01', 'super', role='Admin')
        results = admin_search_cctv_by_invoice(admin, invoice_id=invoice_id)
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['invoice_id'], invoice_id)

    def test_financial_closing_rejected_without_payment(self):
        """اختبار رفض الإقفال بدون دفع الاشتراك"""
        admin = Merchant('A01', 'super', role='Admin')
        merchant = Merchant('M01', 'StoreOne', role='Merchant', is_annual_subscription_paid=False)
        self.platform.balance = Decimal('50.00')
        
        with self.assertRaises(ValueError):
            execute_financial_closing(admin, merchant)
        
        self.assertEqual(self.platform.balance, Decimal('50.00'))

    def test_financial_closing_success_with_payment(self):
        """اختبار نجاح الإقفال المالي"""
        admin = Merchant('A01', 'super', role='Admin')
        merchant = Merchant('M01', 'StoreOne', role='Merchant', is_annual_subscription_paid=True)
        self.platform.balance = Decimal('111.50')
        self.distribution_expense.balance = Decimal('10.00')
        
        res = execute_financial_closing(admin, merchant)
        
        self.assertTrue(res)
        self.assertEqual(self.platform.balance, Decimal('0.00'))
        self.assertEqual(self.distribution_expense.balance, Decimal('0.00'))

    def test_ai_accountant_parse_invoice(self):
        """اختبار محاسب ذكي لتحليل الفاتورة"""
        self.cash.balance = Decimal('0.00')
        before_qty = PRODUCTS['P001']['quantity']
        
        result = ai_parse_and_record_invoice('فاتورة شراء بقيمة 500 ريال وباركود P001')
        
        self.assertEqual(result['product'], 'P001')
        self.assertTrue(Decimal(result['amount']) > 0)
        self.assertTrue(result['qty_added'] >= 1)
        self.assertEqual(PRODUCTS['P001']['quantity'], before_qty + result['qty_added'])

    def test_financial_summary(self):
        """اختبار توليد الملخص المالي"""
        summary = ai_generate_financial_summary()
        
        self.assertIn('total_assets', summary)
        self.assertIn('cash_111', summary)
        self.assertIn('merchant_wallet_116', summary)
        self.assertIn('platform_commissions_417', summary)
        
        Decimal(summary['total_assets'])
        Decimal(summary['cash_111'])

    def test_persistence_save_and_load(self):
        """اختبار ا��حفظ والتحميل من JSON"""
        # إضافة بيانات
        customer = Account('113', 'عملاء_متجر', nature='debit')
        order = buyFromStore('P001', 2, customer, self.sales)
        
        save_all_persistence()
        
        # مسح البيانات
        ORDERS.clear()
        
        # تحميل البيانات
        load_store_db()
        
        self.assertTrue(len(ORDERS) > 0)
        self.assertEqual(ORDERS[0]['invoice_id'], order['invoice_id'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
