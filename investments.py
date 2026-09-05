import sqlite3
import os
import uuid
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'investments.db')

SCHEMA = '''
CREATE TABLE IF NOT EXISTS investments (
    investment_id TEXT PRIMARY KEY,
    owner_user_id TEXT,
    product_code TEXT,
    total_quantity INTEGER,
    remaining_quantity INTEGER,
    amount_locked TEXT,
    unit_price TEXT,
    status TEXT,
    terms_hash TEXT,
    agreement_signature TEXT,
    created_at TEXT,
    closed_at TEXT,
    sales_amount TEXT DEFAULT '0.00'
);
'''


def _conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = _conn()
    cur = conn.cursor()
    cur.executescript(SCHEMA)
    conn.commit()
    conn.close()


def create_investment(owner_user_id, product_code, total_quantity, unit_price, amount_locked, terms_hash, agreement_signature):
    investment_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat() + 'Z'
    conn = _conn()
    cur = conn.cursor()
    cur.execute('''INSERT INTO investments(investment_id, owner_user_id, product_code, total_quantity, remaining_quantity, amount_locked, unit_price, status, terms_hash, agreement_signature, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (investment_id, owner_user_id, product_code, int(total_quantity), int(total_quantity), str(amount_locked), str(unit_price), 'Active', terms_hash, agreement_signature, now))
    conn.commit()
    conn.close()
    return investment_id


def get_active_investments_for_product(product_code):
    conn = _conn()
    cur = conn.cursor()
    cur.execute('SELECT * FROM investments WHERE product_code = ? AND status = ?', (product_code, 'Active'))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_investment(investment_id):
    conn = _conn()
    cur = conn.cursor()
    cur.execute('SELECT * FROM investments WHERE investment_id = ?', (investment_id,))
    r = cur.fetchone()
    conn.close()
    return dict(r) if r else None


def update_investment_remaining(investment_id, new_remaining, add_sales_amount):
    conn = _conn()
    cur = conn.cursor()
    # sales_amount stored as text decimal
    cur.execute('SELECT sales_amount FROM investments WHERE investment_id = ?', (investment_id,))
    row = cur.fetchone()
    prev = row['sales_amount'] if row else '0.00'
    try:
        prev_f = float(prev)
    except Exception:
        prev_f = 0.0
    new_sales = prev_f + float(add_sales_amount)
    cur.execute('UPDATE investments SET remaining_quantity = ?, sales_amount = ? WHERE investment_id = ?', (int(new_remaining), str(new_sales), investment_id))
    conn.commit()
    conn.close()


def close_investment(investment_id):
    # compute net profit and perform accounting transfers via accounting_core
    # import here to avoid circular imports
    from accounting_core import ACCOUNTS, Account, Transaction, save_all_persistence
    inv = get_investment(investment_id)
    if not inv:
        return False
    if inv['status'] == 'Closed':
        return True

    # parse decimals
    try:
        sales_amount = float(inv.get('sales_amount', '0.00'))
    except Exception:
        sales_amount = 0.0
    try:
        amount_locked = float(inv.get('amount_locked', '0.00'))
    except Exception:
        amount_locked = 0.0

    # platform fees allocated need to be stored per-investment; for now assume they were deducted from sales_amount externally
    platform_fee_allocated = 0.0

    net_profit = sales_amount - amount_locked - platform_fee_allocated

    # perform accounting transaction: move funds from INV_HOLD (115) to investor wallet (116...code)
    inv_hold = ACCOUNTS.get('115')
    if not inv_hold:
        inv_hold = Account('115', 'INV_HOLD', nature='debit')
    # create/find investor wallet
    owner = inv.get('owner_user_id')
    wallet_code = f"116{owner[:8]}"
    wallet = ACCOUNTS.get(wallet_code)
    if not wallet:
        wallet = Account(wallet_code, f"Wallet_{owner}", nature='debit')

    # amount to release = amount_locked + net_profit (i.e., total funds to move back to investor)
    total_release = amount_locked + net_profit
    try:
        tx = Transaction(description=f"Close investment {investment_id} for owner {owner}")
        # debit INV_HOLD (increase asset) and credit wallet? Using same pattern as other transactions
        tx.add_entry(inv_hold, 'credit', str(total_release))
        tx.add_entry(wallet, 'debit', str(total_release))
        tx.commit()
    except Exception as e:
        # fail safe: do not change DB status
        return False

    # mark as closed
    conn = _conn()
    cur = conn.cursor()
    cur.execute('UPDATE investments SET status = ?, closed_at = ? WHERE investment_id = ?', ('Closed', datetime.utcnow().isoformat() + 'Z', investment_id))
    conn.commit()
    conn.close()

    # persist accounting
    try:
        save_all_persistence()
    except Exception:
        pass

    return True


def allocate_sale_for_order(order):
    # order expected to have invoice_id, product, quantity, total, platform_fee
    product = order.get('product')
    qty = int(order.get('quantity', 0))
    total = float(order.get('total') or 0.0)
    platform_fee = float(order.get('platform_fee') or 0.0)
    if qty <= 0:
        return
    unit_price = total / qty if qty else 0.0

    # fetch active investments for this product
    invs = get_active_investments_for_product(product)
    remaining_to_allocate = qty
    for inv in invs:
        if remaining_to_allocate <= 0:
            break
        inv_id = inv['investment_id']
        rem = int(inv['remaining_quantity'])
        if rem <= 0:
            continue
        allocate_qty = min(rem, remaining_to_allocate)
        # compute sales amount allocated
        alloc_amount = allocate_qty * unit_price
        # proportion of platform fee
        alloc_fee = platform_fee * (allocate_qty / qty) if qty else 0.0
        # update inv sales and remaining
        new_rem = rem - allocate_qty
        update_investment_remaining(inv_id, new_rem, alloc_amount)
        remaining_to_allocate -= allocate_qty
        # if investment depleted -> close
        if new_rem == 0:
            close_investment(inv_id)

    return True
