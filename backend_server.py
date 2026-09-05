"""
backend_server.py
خادم Flask لـ MetaHOP مع نظام تحقق مبسط: تسجيل/تسجيل دخول/جلسات، وحماية لصفحات إدارية واستثمارية.
تم إضافة:
- تخزين المستخدمين في users.json (مؤقت أثناء التطوير)
- نقاط نهاية: /register/personal, /register/business, /login, /logout
- حماية صفحات: /admin (تحتاج دور Business وstatus Active)، /investments (تحتاج دور Personal)
- تعديل /api/admin/cctv للتحقق من جلسة المستخدم وصلاحياته
- استخدام werkzeug.security لتجزئة كلمات المرور

ملاحظة: تأكد من تغيير SECRET_KEY في البيئة عند النشر.
"""

from flask import Flask, jsonify, request, session, redirect, url_for, send_from_directory, abort
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
import uuid
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
# Change this in production to something secret and coming from env/config
app.secret_key = os.environ.get('SECRET_KEY', 'dev_secret_key_change_me')

# Data files for offline storage (branch: feature/attendance-offline)
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
ATT_JSON = os.path.join(DATA_DIR, 'attendance_offline.json')
WARN_JSON = os.path.join(DATA_DIR, 'warnings_offline.json')
WHATSAPP_JSON = os.path.join(DATA_DIR, 'whatsapp_offline.json')
USERS_JSON = os.path.join(DATA_DIR, 'users.json')
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


# ----------------- Users helpers -----------------
def load_users():
    users = _read_json(USERS_JSON)
    if not isinstance(users, list):
        users = []
    return users


def save_users(users):
    _write_json(USERS_JSON, users)


def find_user_by_id(user_id):
    users = load_users()
    for u in users:
        if u.get('id') == user_id:
            return u
    return None


def find_user_by_identifier(identifier):
    # identifier can be email or username
    users = load_users()
    for u in users:
        if u.get('email') == identifier or u.get('username') == identifier:
            return u
    return None


def create_user(user_obj):
    users = load_users()
    users.append(user_obj)
    save_users(users)
    return user_obj


# ----------------- Initialization -----------------
@app.before_request
def initialize():
    if not hasattr(app, 'initialized'):
        load_store_db()
        load_invest_db()
        # ensure users.json exists
        if not os.path.exists(USERS_JSON):
            save_users([])
        app.initialized = True


# ----------------- Authentication Routes -----------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        # serve login page file
        return send_from_directory(os.path.dirname(__file__), 'login.html')

    data = request.get_json() or request.form or {}
    identifier = data.get('identifier') or data.get('email') or data.get('username')
    password = data.get('password')

    if not identifier or not password:
        return jsonify({'status': 'error', 'message': 'identifier and password required'}), 400

    user = find_user_by_identifier(identifier)
    if not user:
        return jsonify({'status': 'error', 'message': 'user not found'}), 404

    if not check_password_hash(user.get('password_hash', ''), password):
        return jsonify({'status': 'error', 'message': 'invalid credentials'}), 401

    if user.get('role') == 'Business' and user.get('status') != 'Active':
        return jsonify({'status': 'error', 'message': 'Business account pending activation'}), 403

    # set session
    session['user_id'] = user['id']
    session['role'] = user.get('role')

    # route based on role
    if user.get('role') == 'Business':
        return jsonify({'status': 'success', 'message': 'Logged in', 'redirect': '/admin'}), 200
    else:
        return jsonify({'status': 'success', 'message': 'Logged in', 'redirect': '/investments'}), 200


@app.route('/logout', methods=['POST', 'GET'])
def logout():
    session.pop('user_id', None)
    session.pop('role', None)
    return redirect('/login')


@app.route('/register/personal', methods=['GET', 'POST'])
def register_personal():
    if request.method == 'GET':
        return send_from_directory(os.path.dirname(__file__), 'register_personal.html')

    data = request.get_json() or request.form or {}
    username = data.get('username')
    email = data.get('email')
    phone = data.get('phone')
    password = data.get('password')
    confirm = data.get('confirm_password') or data.get('confirm')

    if not username or not email or not password or not confirm:
        return jsonify({'status': 'error', 'message': 'missing required fields'}), 400

    if password != confirm:
        return jsonify({'status': 'error', 'message': 'passwords do not match'}), 400

    if find_user_by_identifier(email) or find_user_by_identifier(username):
        return jsonify({'status': 'error', 'message': 'user already exists'}), 400

    user_obj = {
        'id': str(uuid.uuid4()),
        'type': 'personal',
        'username': username,
        'email': email,
        'phone': phone,
        'password_hash': generate_password_hash(password),
        'role': 'Personal',
        'status': 'Active',
        'created_at': datetime.utcnow().isoformat() + 'Z'
    }

    create_user(user_obj)

    # auto-login personal user
    session['user_id'] = user_obj['id']
    session['role'] = user_obj['role']

    return jsonify({'status': 'success', 'message': 'Personal account created', 'redirect': '/investments'}), 201


@app.route('/register/business', methods=['GET', 'POST'])
def register_business():
    if request.method == 'GET':
        return send_from_directory(os.path.dirname(__file__), 'register_business.html')

    data = request.get_json() or request.form or {}
    company_name = data.get('company_name')
    tax_number = data.get('tax_number')
    commercial_registration = data.get('commercial_registration')
    company_email = data.get('company_email')
    manager_phone = data.get('manager_phone')
    password = data.get('password')
    confirm = data.get('confirm_password') or data.get('confirm')

    if not all([company_name, tax_number, commercial_registration, company_email, manager_phone, password, confirm]):
        return jsonify({'status': 'error', 'message': 'missing required fields'}), 400

    if password != confirm:
        return jsonify({'status': 'error', 'message': 'passwords do not match'}), 400

    if find_user_by_identifier(company_email):
        return jsonify({'status': 'error', 'message': 'company email already registered'}), 400

    user_obj = {
        'id': str(uuid.uuid4()),
        'type': 'business',
        'company_name': company_name,
        'tax_number': tax_number,
        'commercial_registration': commercial_registration,
        'email': company_email,
        'manager_phone': manager_phone,
        'password_hash': generate_password_hash(password),
        'role': 'Business',
        'status': 'Pending',  # important: pending until admin activates
        'created_at': datetime.utcnow().isoformat() + 'Z'
    }

    create_user(user_obj)

    return jsonify({'status': 'success', 'message': 'Business account created, pending activation by admin'}), 201


# ----------------- Protected page routes -----------------
def require_login(role_required=None):
    def decorator(f):
        def wrapper(*args, **kwargs):
            user_id = session.get('user_id')
            if not user_id:
                return redirect('/login')
            user = find_user_by_id(user_id)
            if not user:
                session.pop('user_id', None)
                session.pop('role', None)
                return redirect('/login')
            if role_required and user.get('role') != role_required:
                abort(403)
            return f(*args, **kwargs)
        wrapper.__name__ = f.__name__
        return wrapper
    return decorator


@app.route('/admin', methods=['GET'])
@require_login(role_required='Business')
def admin_page():
    # serve the admin.html file from repo only to logged-in Business users
    return send_from_directory(os.path.dirname(__file__), 'admin.html')


@app.route('/investments', methods=['GET'])
@require_login(role_required='Personal')
def investments_page():
    return send_from_directory(os.path.dirname(__file__), 'investments.html')


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
    """تنفيذ تسجيل الحضور (existing code preserved)"""
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
    """البحث في سجلات الكاميرا (للمدير فقط) - الآن محمي عبر الجلسات"""
    try:
        # ensure logged in business user
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'status': 'error', 'message': 'authentication required'}), 401
        user = find_user_by_id(user_id)
        if not user or user.get('role') != 'Business' or user.get('status') != 'Active':
            return jsonify({'status': 'error', 'message': 'admin privileges required'}), 403

        invoice_id = request.args.get('invoice_id')
        date_str = request.args.get('date')
        
        if not invoice_id and not date_str:
            return jsonify({'status': 'error', 'message': 'أدخل رقم فاتورة أو تاريخ'}), 400
        
        results = admin_search_cctv_by_invoice(Merchant(user_id, user.get('company_name','Admin'), role='Admin'), invoice_id=invoice_id, date_str=date_str)
        
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
