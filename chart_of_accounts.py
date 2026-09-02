class SalesSystem:
    def __init__(self):
        self.journal_entries = [] # دفتر القيود اليومية لـ "ميتا هوب"

    # دالة تسجيل فاتورة البيع (نقداً أو آجل)
    def create_sales_invoice(self, invoice_type, amount, customer_name=None):
        if amount <= 0:
            raise ValueError("قيمة الفاتورة يجب أن تكون أكبر من صفر")
        
        if invoice_type == "نقداً":
            # قيد الفاتورة النقدية: من 111 الصندوق إلى 411 المبيعات
            entry = {"debit": "111_الصندوق", "credit": "411_المبيعات", "amount": amount}
        elif invoice_type == "آجل":
            if not customer_name:
                raise ValueError("يجب تحديد اسم العميل في الفاتورة الآجلة")
            # قيد الفاتورة الآجلة: من 113 العملاء إلى 411 المبيعات
            entry = {"debit": f"113_العملاء_{customer_name}", "credit": "411_المبيعات", "amount": amount}
        else:
            raise ValueError("نوع الفاتورة غير صحيح")
            
        self.journal_entries.append(entry)
        return "تم تسجيل الفاتورة بنجاح"

    # دالة سداد العميل (سند قبض)
    def receive_payment(self, customer_name, amount):
        # من 111 الصندوق إلى 113 العملاء
        entry = {"debit": "111_الصندوق", "credit": f"113_العملاء_{customer_name}", "amount": amount}
        self.journal_entries.append(entry)
        return "تم تسجيل سند القبض بنجاح"
