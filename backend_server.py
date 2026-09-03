"""
backend_server.py
خادم Flask لـ MetaHOP مع 5 نقاط API رئيسية
"""

from flask import Flask, jsonify, request
from accounting_core import (
    load_store_db, load_invest_db, save_all_persistence,
    PRODUCTS, ACCOUNTS, ORDERS, CCTV_INVOICE_LOGS, ATTENDANCE_LOGS, 
    CHAT_MESSAGE_LOGS, WHATSAPP_NOTIFICATIONS,
    Account, Employee, Merchant, Transaction,
    get_products, buyFromStore, admin_search_cctv_by_invoice,
    record_attendance_biometric, send_in_app_message, send_whatsapp_notification,
    pay_salary, ai_generate_financial_summary, decimal_to_str
)
from decimal import Decimal

app = Flask(__name__)

# تحميل البيانات عند بدء السيرفر
@app.before_request
def initialize():
    if not hasattr(app, 'initialized'):
        load_store_db()
        load_invest_db()
        app.initialized = True


# ========== API 1: GET /api/products - السلة والمتجر ==========
@app.route('/api/products', methods=['GET'])
def get_store_products():
    """عرض المنتجات الحالية من المتجر"""
    try:
        products = get_products()
        return jsonify({
            'status': 'success',
            'products': products,
            'count': len(products)
        }), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ========== API 2: POST /api/buy - الشراء الفوري ==========
@app.route('/api/buy', methods=['POST'])
def buy_product():
    """تنفيذ عملية شراء من المتجر"""
    try:
        data = request.get_json()
        
        product_code = data.get('product_code')
        quantity = data.get('quantity', 1)
        customer_phone = data.get('customer_phone')
        
        if not product_code or product_code not in PRODUCTS:
            return jsonify({'status': 'error', 'message': 'المنتج غير موجود'}), 404
        
        if quantity <= 0:
            return jsonify({'status': 'error', 'message': 'الكمية يجب أن تكون موجبة'}), 400
        
        # إنشاء حسابات العميل والمبيعات
        customer_account = ACCOUNTS.get('113') or Account('113', 'عملاء_متجر', nature='debit')
        sales_account = ACCOUNTS.get('411') or Account('411', 'مبيعات_متجر', nature='credit')
        
        # تنفيذ الشراء
        order = buyFromStore(
            product_code=product_code,
            quantity=int(quantity),
            customer_account=customer_account,
            sales_account=sales_account,
            customer_phone=customer_phone,
            inventory_station='121'
        )
        
        save_all_persistence()
        
        return jsonify({
            'status': 'success',
            'message': 'تم الشراء بنجاح',
            'invoice_id': order['invoice_id'],
            'total': order['total'],
            'product': order['product'],
            'quantity': order['quantity'],
            'platform_fee': order['platform_fee']
        }), 201
    
    except ValueError as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ========== API 3: POST /api/attendance - بصمة الموظف ==========
@app.route('/api/attendance', methods=['POST'])
def record_attendance():
    """تسجيل بصمة الموظف (دخول/خروج) مع خصم التأخير"""
    try:
        data = request.get_json()
        
        emp_id = data.get('emp_id')
        emp_name = data.get('emp_name', 'موظف')
        base_salary = data.get('base_salary', '0')
        movement_type = data.get('movement_type')  # check_in أو check_out
        time_str = data.get('time')  # HH:MM
        date_str = data.get('date')  # YYYY-MM-DD
        phone_number = data.get('phone_number')
        
        if not emp_id or movement_type not in ('check_in', 'check_out'):
            return jsonify({'status': 'error', 'message': 'بيانات غير صحيحة'}), 400
        
        if not time_str or not date_str:
            return jsonify({'status': 'error', 'message': 'الوقت والتاريخ مطلوبان'}), 400
        
        # إنشاء كائن موظف
        employee = Employee(emp_id, emp_name, base_salary, phone_number)
        
        # تسجيل البصمة
        attendance_record = record_attendance_biometric(
            emp_id=emp_id,
            employee=employee,
            movement_type=movement_type,
            time_str=time_str,
            date_str=date_str
        )
        
        save_all_persistence()
        
        return jsonify({
            'status': 'success',
            'message': 'تم تسجيل البصمة بنجاح',
            'emp_id': attendance_record['emp_id'],
            'emp_name': attendance_record['emp_name'],
            'movement_type': attendance_record['movement_type'],
            'time': attendance_record['time'],
            'is_late': attendance_record['is_late'],
            'deduction_amount': attendance_record['deduction_amount']
        }), 201
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ========== API 4: POST /api/chat - الدردشة والمراسلة ==========
@app.route('/api/chat', methods=['POST'])
def send_message():
    """إرسال رسالة فورية داخل التطبيق"""
    try:
        data = request.get_json()
        
        sender = data.get('sender')
        receiver = data.get('receiver')
        text = data.get('text')
        
        if not sender or not receiver or not text:
            return jsonify({'status': 'error', 'message': 'المرسل والمستقبل والنص مطلوبان'}), 400
        
        message = send_in_app_message(sender, receiver, text)
        
        save_all_persistence()
        
        return jsonify({
            'status': 'success',
            'message': 'تم إرسال الرسالة',
            'sender': message['sender'],
            'receiver': message['receiver'],
            'text': message['text'],
            'time': message['time'],
            'status': message['status']
        }), 201
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/chat/<receiver>', methods=['GET'])
def get_messages(receiver):
    """الحصول على الرسائل الموجهة لمستقبل معين"""
    try:
        messages = [m for m in CHAT_MESSAGE_LOGS if m['receiver'] == receiver]
        return jsonify({
            'status': 'success',
            'receiver': receiver,
            'messages': messages,
            'count': len(messages)
        }), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ========== API 5: GET /api/admin/cctv - بحث الكاميرات للإدمن ==========
@app.route('/api/admin/cctv', methods=['GET'])
def search_cctv():
    """البحث في سجلات الكاميرات (للمدير فقط)"""
    try:
        admin_id = request.args.get('admin_id')
        invoice_id = request.args.get('invoice_id')
        date_str = request.args.get('date')
        
        if not admin_id:
            return jsonify({'status': 'error', 'message': 'معرف الإدمن مطلوب'}), 400
        
        # التحقق من أن المستخدم إدمن
        admin = Merchant(admin_id, 'Admin', role='Admin')
        
        if not invoice_id and not date_str:
            return jsonify({'status': 'error', 'message': 'أدخل رقم فاتورة أو تاريخ'}), 400
        
        results = admin_search_cctv_by_invoice(admin, invoice_id=invoice_id, date_str=date_str)
        
        return jsonify({
            'status': 'success',
            'search_type': 'invoice' if invoice_id else 'date',
            'query': invoice_id or date_str,
            'results': results,
            'count': len(results)
        }), 200
    
    except PermissionError as e:
        return jsonify({'status': 'error', 'message': str(e)}), 403
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ========== API إضافية: الملخص المالي والإشعارات ==========

@app.route('/api/summary', methods=['GET'])
def financial_summary():
    """الملخص المالي الشامل"""
    try:
        summary = ai_generate_financial_summary()
        return jsonify({
            'status': 'success',
            'summary': summary
        }), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/orders', methods=['GET'])
def get_orders():
    """الحصول على قائمة الطلبات"""
    try:
        return jsonify({
            'status': 'success',
            'orders': ORDERS,
            'count': len(ORDERS)
        }), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/attendance/logs', methods=['GET'])
def get_attendance_logs():
    """الحصول على سجلات البصمة"""
    try:
        emp_id = request.args.get('emp_id')
        if emp_id:
            logs = [log for log in ATTENDANCE_LOGS if log['emp_id'] == emp_id]
        else:
            logs = ATTENDANCE_LOGS
        
        return jsonify({
            'status': 'success',
            'logs': logs,
            'count': len(logs)
        }), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/notifications/whatsapp', methods=['GET'])
def get_whatsapp_notifications():
    """الحصول على سجلات إشعارات واتساب"""
    try:
        phone = request.args.get('phone')
        if phone:
            notifs = [n for n in WHATSAPP_NOTIFICATIONS if n['recipient_phone'] == phone]
        else:
            notifs = WHATSAPP_NOTIFICATIONS
        
        return jsonify({
            'status': 'success',
            'notifications': notifs,
            'count': len(notifs)
        }), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ========== معالجة الأخطاء ==========

@app.errorhandler(404)
def not_found(error):
    return jsonify({'status': 'error', 'message': 'الصفحة غير موجودة'}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({'status': 'error', 'message': 'خطأ في السيرفر'}), 500


if __name__ == '__main__':
    print("🚀 بدء تشغيل خادم MetaHOP على http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)
