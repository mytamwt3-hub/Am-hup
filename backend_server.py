"""
backend_server.py
MetaHOP Flask server — extended with:
- SECRET_KEY from environment
- admin password_hash auto-generation (if missing) using werkzeug.generate_password_hash
- KYC stub endpoints: /kyc/start, /kyc/verify
- Investment creation endpoint: /invest/create (requires owner KYC verified)
- Integrates with investments.sqlite via investments.create_investment and accounting_core Transaction

Security notes:
- ADMIN_PASSWORD can be provided via env var ADMIN_PASSWORD; otherwise default temporary password is used (MetaUpPass2026!).
- Ensure SECRET_KEY is set in environment for production.
"""

from flask import Flask, jsonify, request, redirect, send_from_directory, abort
from accounting_core import (
    load_store_db, load_invest_db, save_all_persistence,
    PRODUCTS, ACCOUNTS, ORDERS, CCTV_INVOICE_LOGS, ATTENDANCE_LOGS,
    CHAT_MESSAGE_LOGS, WHATSAPP_NOTIFICATIONS,
    Account, Employee, Merchant, Transaction,
    get_products, buyFromStore, admin_search_cctv_by_invoice,
    record_attendance_biometric, send_in_app_message, send_whatsapp_notification,
    pay_salary, ai_generate_financial_summary, decimal_to_str
)
from investments import init_db, create_investment, get_investment
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, timedelta
import os
import json
import uuid
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
# SECRET_KEY must be provided by environment in production
app.secret_key = os.environ.get('SECRET_KEY', os.environ.get('FLASK_SECRET', 'dev_secret_key_change_me'))

# Data directory and files
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
USERS_JSON = os.path.join(DATA_DIR, 'users.json')
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


# Users helpers (file-based for development — migrate to central DB in production)
def load_users():
    users = _read_json(USERS_JSON)
    if not isinstance(users, list):
        users = []
    return users


def save_users(users):
    _write_json(USERS_JSON, users)


def find_user_by_email(email):
    users = load_users()
    for u in users:
        if u.get('email') == email:
            return u
    return None


def ensure_admin_password():
    # If admin user exists and password_hash empty, generate hash from env ADMIN_PASSWORD or default
    users = load_users()
    changed = False
    admin_email = 'mytamwt3@gmail.com'
    default_pw = os.environ.get('ADMIN_PASSWORD', 'MetaUpPass2026!')
    for user in users:
        if user.get('email') == admin_email:
            if not user.get('password_hash'):
                # generate password hash and persist
                ph = generate_password_hash(default_pw)
                user['password_hash'] = ph
                changed = True
    if changed:
        save_users(users)
    return


# Initialize DBs and load persisted data
@app.before_request
def initialize():
    if not hasattr(app, 'initialized'):
        # initialize accounting DBs
        load_store_db()
        load_invest_db()
        # initialize investments sqlite
        try:
            init_db()
        except Exception:
            pass
        # ensure users.json exists
        if not os.path.exists(USERS_JSON):
            # create default admin stub
            admin_user = {
                'id': 'admin',
                'username': 'admin',
                'email': 'mytamwt3@gmail.com',
                'password_hash': '',
                'role': 'Business',
                'status': 'Active',
                'kyc_verified': True,
                'created_at': datetime.utcnow().isoformat() + 'Z'
            }
            save_users([admin_user])
        # generate admin password_hash if missing using ADMIN_PASSWORD env or default
        try:
            ensure_admin_password()
        except Exception:
            pass
        app.initialized = True


# ========== KYC Stub endpoints ==========
@app.route('/kyc/start', methods=['GET'])
def kyc_start():
    """Start a KYC session. Returns a session_id for the front-end to use with getUserMedia stream."""
    session_id = str(uuid.uuid4())
    # In production, record session metadata and expire it
    return jsonify({'status': 'success', 'session_id': session_id}), 200


@app.route('/kyc/verify', methods=['POST'])
def kyc_verify():
    """KYC stub: verify user identity based on a live capture. Expects JSON: {email, session_id, liveness:true}
    In production this endpoint will forward frames to third-party KYC provider (Sumsub/IDAnalyzer).
    """
    data = request.get_json() or {}
    email = data.get('email')
    session_id = data.get('session_id')
    liveness = data.get('liveness', False)

    if not email or not session_id:
        return jsonify({'status': 'error', 'message': 'email and session_id required'}), 400

    user = find_user_by_email(email)
    if not user:
        return jsonify({'status': 'error', 'message': 'user not found'}), 404

    # KYC stub logic: accept if liveness == True
    if liveness:
        user['kyc_verified'] = True
        users = load_users()
        for u in users:
            if u.get('email') == email:
                u['kyc_verified'] = True
        save_users(users)
        return jsonify({'status': 'success', 'message': 'KYC verified'}), 200
    else:
        return jsonify({'status': 'error', 'message': 'KYC failed (liveness=false)'}), 400


# ========== Investment creation endpoint ==========
@app.route('/invest/create', methods=['POST'])
def invest_create():
    """Create an investment and lock funds into INV_HOLD (account 115).
    Expects JSON: {email, product_code, total_quantity, unit_price, terms_hash, agreement_signature}
    """
    data = request.get_json() or {}
    email = data.get('email')
    product_code = data.get('product_code')
    total_qty = data.get('total_quantity')
    unit_price = data.get('unit_price')
    terms_hash = data.get('terms_hash')
    agreement_signature = data.get('agreement_signature')

    if not all([email, product_code, total_qty, unit_price, terms_hash, agreement_signature]):
        return jsonify({'status': 'error', 'message': 'missing required fields'}), 400

    user = find_user_by_email(email)
    if not user:
        return jsonify({'status': 'error', 'message': 'user not found'}), 404

    if not user.get('kyc_verified'):
        return jsonify({'status': 'error', 'message': 'KYC required before investment'},), 403

    try:
        qty = int(total_qty)
        price = Decimal(str(unit_price))
        amount_locked = (price * Decimal(qty)).quantize(Decimal('0.01'))
    except Exception as e:
        return jsonify({'status': 'error', 'message': 'invalid numeric fields'}), 400

    # prepare accounting entries: move funds from customer account (113) to INV_HOLD (115)
    customer_account = ACCOUNTS.get('113') or Account('113', 'عملاء_متجر', nature='debit')
    inv_hold = ACCOUNTS.get('115') or Account('115', 'INV_HOLD', nature='debit')

    try:
        tx = Transaction(description=f"Lock funds for investment by {email}")
        # debit INV_HOLD (increase asset), credit customer (decrease customer balance)
        tx.add_entry(inv_hold, 'debit', str(amount_locked))
        tx.add_entry(customer_account, 'credit', str(amount_locked))
        tx.commit()
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'accounting error: {str(e)}'}), 500

    # create investment record in sqlite
    inv_id = None
    try:
        inv_id = create_investment(user['id'], product_code, qty, str(price), str(amount_locked), terms_hash, agreement_signature)
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'investment creation failed: {str(e)}'}), 500

    return jsonify({'status': 'success', 'investment_id': inv_id, 'amount_locked': str(amount_locked)}), 201


# ========== Expose registration/login stubs for testing ==========
@app.route('/login', methods=['GET', 'POST'])
def login_route():
    if request.method == 'GET':
        return send_from_directory(os.path.dirname(__file__), 'login.html')
    data = request.get_json() or {}
    identifier = data.get('identifier') or data.get('email') or data.get('username')
    password = data.get('password')
    if not identifier or not password:
        return jsonify({'status': 'error', 'message': 'identifier and password required'}), 400
    # find user by email or username
    users = load_users()
    user = None
    for u in users:
        if u.get('email') == identifier or u.get('username') == identifier:
            user = u
            break
    if not user:
        return jsonify({'status': 'error', 'message': 'user not found'}), 404
    ph = user.get('password_hash') or ''
    if not ph:
        return jsonify({'status': 'error', 'message': 'password not set for user'}), 403
    if not check_password_hash(ph, password):
        return jsonify({'status': 'error', 'message': 'invalid credentials'}), 401
    # for testing, return simple success
    if user.get('role') == 'Business':
        return jsonify({'status': 'success', 'redirect': '/admin'}), 200
    return jsonify({'status': 'success', 'redirect': '/investments'}), 200


# small admin endpoint to list users (protected by admin password via basic check)
@app.route('/admin/users', methods=['GET'])
def admin_list_users():
    auth = request.authorization
    if not auth:
        return jsonify({'status': 'error', 'message': 'authorization required'}), 401
    users = load_users()
    admin_user = None
    for u in users:
        if u.get('email') == 'mytamwt3@gmail.com':
            admin_user = u
    if not admin_user or not check_password_hash(admin_user.get('password_hash',''), auth.password):
        return jsonify({'status': 'error', 'message': 'admin auth failed'}), 403
    # return minimal users list
    safe = [{k: v for k, v in u.items() if k != 'password_hash'} for u in users]
    return jsonify({'status': 'success', 'users': safe}), 200


# ========== existing APIs (kept) ==========
@app.route('/api/products', methods=['GET'])
def get_store_products():
    try:
        products = get_products()
        return jsonify({'status': 'success', 'products': products, 'count': len(products)}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/buy', methods=['POST'])
def buy_product():
    try:
        data = request.get_json()
        product_code = data.get('product_code')
        quantity = data.get('quantity', 1)
        customer_phone = data.get('customer_phone')
        if not product_code or product_code not in PRODUCTS:
            return jsonify({'status': 'error', 'message': 'المنتج غير موجود'}), 404
        if quantity <= 0:
            return jsonify({'status': 'error', 'message': 'الكمية يجب أن تكون موجبة'}), 400
        customer_account = ACCOUNTS.get('113') or Account('113', 'عملاء_متجر', nature='debit')
        sales_account = ACCOUNTS.get('411') or Account('411', 'مبيعات_متجر', nature='credit')
        order = buyFromStore(product_code=product_code, quantity=int(quantity), customer_account=customer_account, sales_account=sales_account, customer_phone=customer_phone, inventory_station='121')
        save_all_persistence()
        return jsonify({'status': 'success', 'message': 'تم الشراء بنجاح', 'invoice_id': order['invoice_id'], 'total': order['total'], 'product': order['product'], 'quantity': order['quantity'], 'platform_fee': order['platform_fee']}), 201
    except ValueError as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ========== error handlers ==========
@app.errorhandler(404)
def not_found(error):
    return jsonify({'status': 'error', 'message': 'الصفحة غير موجودة'}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({'status': 'error', 'message': 'خطأ في السيرفر'}), 500


if __name__ == '__main__':
    print("🚀 بدء تشغيل خادم MetaHOP على http://localhost:5000")
    print("🔐 تأكد من تعيين SECRET_KEY في البيئة للبيئات الحقيقية")
    app.run(host='0.0.0.0', port=5000, debug=True)
