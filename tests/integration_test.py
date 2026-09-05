"""tests/integration_test.py
Integration test for MetaHUP investment flow (local, no HTTP server required).
Run this script from the repository root after installing requirements (Flask, werkzeug).
It simulates:
 - init DBs
 - create accounts and a product
 - create a test investor, lock funds into INV_HOLD (115)
 - create an investment record via investments.create_investment
 - simulate sales via buyFromStore that allocate to the investment
 - check that investment closes when remaining_quantity == 0
 - print account balances and investment status

Note: This script uses internal modules and mutates the repo's data files (store_db.json, invest_db.json, data/*.json).
Use on a development copy or after making a git branch.
"""

from accounting_core import add_product, ACCOUNTS, Account, save_all_persistence, buyFromStore, get_products
from investments import init_db, create_investment, get_investment
from decimal import Decimal
import os

print('Initializing investment DB...')
init_db()

# Ensure accounts exist
ACCOUNTS.setdefault('113', Account('113', 'عملاء_متجر', nature='debit'))
ACCOUNTS.setdefault('115', Account('115', 'INV_HOLD', nature='debit'))
ACCOUNTS.setdefault('417', Account('417', 'عمولة_المنصة', nature='credit'))
ACCOUNTS.setdefault('411', Account('411', 'مبيعات_متجر', nature='credit'))

print('Adding product P_TEST with quantity 100 and price 10.00')
add_product('P_TEST', 'Product Test', '10.00', 100)

# Prepare test investor
owner_id = 'test-investor-1'
user_email = 'investor1@example.local'

# Initial customer account balance simulation: we will credit customer's account (113) so the lock can debit it.
# In this simplified simulation, ACCOUNTS balances are naive; set a positive balance on customer account to allow crediting.
# Note: In real system customer balances are tracked per-customer; here we use account 113 as a pooled account.
ACCOUNTS['113'].balance = Decimal('1000.00')
print('Initial balances:')
for code, acc in ACCOUNTS.items():
    print(code, acc.name, acc.balance)

# Create investment: lock 20 units at 10.00 => amount_locked = 200.00
total_qty = 20
unit_price = Decimal('10.00')
amount_locked = unit_price * total_qty

from accounting_core import Transaction
print('\nLocking funds: moving', amount_locked, 'from account 113 to INV_HOLD (115)')
try:
    tx = Transaction(description=f"Test: lock funds for {owner_id}")
    tx.add_entry(ACCOUNTS['115'], 'debit', str(amount_locked))
    tx.add_entry(ACCOUNTS['113'], 'credit', str(amount_locked))
    tx.commit()
except Exception as e:
    print('Accounting error during lock:', e)
    raise

print('Balances after lock:')
for code, acc in ACCOUNTS.items():
    print(code, acc.name, acc.balance)

print('\nCreating investment record in sqlite...')
inv_id = create_investment(owner_id, 'P_TEST', total_qty, str(unit_price), str(amount_locked), 'terms_hash_example', 'agreement_sig_example')
print('Created investment', inv_id)

print('\nSimulating sale of 20 units via buyFromStore (will allocate to investment)')
from accounting_core import Account as ACCT
customer_account = ACCOUNTS.get('113')
sales_account = ACCOUNTS.get('411')
order = buyFromStore('P_TEST', quantity=20, customer_account=customer_account, sales_account=sales_account, customer_phone='0500000000', inventory_station='121')
print('Order created:', order)

print('\nChecking investment status after allocation...')
inv = get_investment(inv_id)
print('Investment record:', inv)

print('\nFinal account balances:')
for code, acc in sorted(ACCOUNTS.items()):
    print(code, acc.name, acc.balance)

print('\nTest complete. Inspect invest_db.json, store_db.json, and data/ files for persistence.')
