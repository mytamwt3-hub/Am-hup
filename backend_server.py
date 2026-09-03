"""
backend_server.py
خادم Flask لـ MetaHOP مع 5 نقاط API رئيسية
تم تحديث نقطة /api/attendance على فرع feature/attendance-offline: حساب دقائق التأخير بالـ Decimal، حفظ أوفلاين في مجلد data كـ JSON، ومنطق تحذير تراكمي وإعداد رسالة واتساب.
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
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, timedelta
import os
import json

app = Flask(__name__)

# Data files for offline storage (branch: feature/attendance-offline)
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
ATT_JSON = os.path.join(DATA_DIR, 'attendance_offline.json')
WARN_JSON = os.path.join(DATA_DIR, 'warnings_offline.json')
WHATSAPP_JSON = os.path.join(DATA_DIR, 'whatsapp_offline.json')
os.makedirs(DATA_DIR, exist_ok=True)


def _read_json(path):
    try:
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception:
        pass
    return []


def _write_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


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


# ====== API 3: POST /api/attendance - بصمة الموظف (محدثة: تخزين أوفلاين، حساب Decimal، إنذارات واتساب) ======
@app.route('/api/attendance', methods=['POST'])
def record_attendance():
    """تسجيل بصمة الموظف (دخول/خروج) مع حساب دقائق التأخير بالـ Decimal، حفظ أوفلاين، ومنطق التحذير التراكمي + إشعار واتساب."""
    try:
        data = request.get_json() or {}
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

        # parse Decimal salary
        try:
            base_salary_d = Decimal(str(base_salary))
        except Exception:
            base_salary_d = Decimal('0')

        # parse time into minutes-from-midnight using Decimal for precision
        try:
            hh, mm = [int(p) for p in time_str.split(':')][:2]
            provided_minutes = Decimal(hh * 60 + mm)
        except Exception:
            return jsonify({'status': 'error', 'message': 'صيغة الوقت غير صحيحة'}), 400

        expected_minutes = Decimal(9 * 60)  # 09:00 => 540
        delay_minutes = provided_minutes - expected_minutes
        if delay_minutes < 0:
            delay_minutes = Decimal('0')
        delay_minutes = delay_minutes.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        # حساب خصم تقريبي للوقت المتأخر: افتراض 22 يوم عمل أو يمكنك تعديل ذلك
        try:
            daily_rate = (base_salary_d / Decimal('22')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            per_minute = (daily_rate / (Decimal('8') * Decimal('60'))).quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)
            deduction_amount = (per_minute * delay_minutes).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        except Exception:
            deduction_amount = Decimal('0.00')

        # بناء سجل الحضور
        attendance_record = {
            'emp_id': emp_id,
            'emp_name': emp_name,
            'movement_type': movement_type,
            'date': date_str,
            'time': time_str,
            'delay_minutes': float(delay_minutes),
            'deduction_amount': float(deduction_amount),
            'phone_number': phone_number,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }

        # append to in-memory global list if exists
        try:
            ATTENDANCE_LOGS.append(attendance_record)
        except Exception:
            pass

        # save offline
        offline_att = _read_json(ATT_JSON)
        offline_att.append(attendance_record)
        _write_json(ATT_JSON, offline_att)

        # cumulative warnings logic
        warnings_store = _read_json(WARN_JSON)
        if not isinstance(warnings_store, dict):
            warnings_store = {}

        emp_warn = warnings_store.get(emp_id, {'events': [], 'last_notified': None})

        WARNING_THRESHOLD_MIN = Decimal('10')
        WINDOW_DAYS = 30
        MAX_WARNINGS = 3

        now_iso = datetime.utcnow().isoformat() + 'Z'

        if movement_type == 'check_in' and delay_minutes >= WARNING_THRESHOLD_MIN:
            emp_warn['events'].append(now_iso)

        # cleanup old events
        window_start = datetime.utcnow() - timedelta(days=WINDOW_DAYS)
        emp_warn['events'] = [ts for ts in emp_warn['events'] if datetime.fromisoformat(ts.replace('Z','')) >= window_start]

        # if reached threshold, send whatsapp warning (respect cooldown)
        if len(emp_warn['events']) >= MAX_WARNINGS:
            send_cooldown_hours = 24
            can_send = True
            last = emp_warn.get('last_notified')
            if last:
                try:
                    last_dt = datetime.fromisoformat(last.replace('Z',''))
                    if datetime.utcnow() - last_dt < timedelta(hours=send_cooldown_hours):
                        can_send = False
                except Exception:
                    can_send = True

            if can_send and phone_number:
                # craft message
                message = (
                    f"مرحباً {emp_name},\n"
                    f"سجل لدينا {len(emp_warn['events'])} حالات تأخير خلال آخر {WINDOW_DAYS} يوم.\n"
                    f"يرجى الالتزام بمواعيد الحضور لتفادي الإجراءات الإدارية.\n"
                    f"للمساعدة تواصل مع الموارد البشرية."
                )

                # call accounting_core helper (it will record a whatsapp notification internally) - signature expects structured params
                try:
                    send_res = send_whatsapp_notification(
                        recipient_phone=phone_number,
                        recipient_type='employee',
                        recipient_name=emp_name,
                        transaction_type='warning',
                        amount='0.00',
                        employee_id=emp_id
                    )
                except Exception as ex:
                    send_res = {'status': 'failed', 'error': str(ex)}

                notif = {
                    'recipient_phone': phone_number,
                    'emp_id': emp_id,
                    'emp_name': emp_name,
                    'message': message,
                    'sent_at': now_iso,
                    'result': send_res
                }

                try:
                    WHATSAPP_NOTIFICATIONS.append(notif)
                except Exception:
                    pass

                w_off = _read_json(WHATSAPP_JSON)
                w_off.append(notif)
                _write_json(WHATSAPP_JSON, w_off)

                emp_warn['last_notified'] = now_iso

        warnings_store[emp_id] = emp_warn
        _write_json(WARN_JSON, warnings_store)

        # persist
        try:
            save_all_persistence()
        except Exception:
            pass

        return jsonify({
            'status': 'success',
            'message': 'تم تسجيل البصمة بنجاح',
            'attendance': attendance_record,
            'warnings_count': len(emp_warn['events']),
            'warning_threshold': MAX_WARNINGS
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
    """البحث في سجلات الكاميرا (للمدير فقط)"""
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


# ... بقية الملف يبقى كما هو (get logs, notifications, error handlers, main)
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
