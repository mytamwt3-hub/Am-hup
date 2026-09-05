@@
     if not all([email, product_code, total_qty, unit_price, terms_hash, agreement_signature]):
         return jsonify({'status': 'error', 'message': 'missing required fields'}), 400
@@
     user = find_user_by_email(email)
     if not user:
         return jsonify({'status': 'error', 'message': 'user not found'}), 404
@@
     try:
         qty = int(total_qty)
         price = Decimal(str(unit_price))
         amount_locked = (price * Decimal(qty)).quantize(Decimal('0.01'))
     except Exception as e:
         return jsonify({'status': 'error', 'message': 'invalid numeric fields'}), 400
@@
     try:
         tx = Transaction(description=f"Lock funds for investment by {email}")
         # debit INV_HOLD (increase asset), credit customer (decrease customer balance)
         tx.add_entry(inv_hold, 'debit', str(amount_locked))
         tx.add_entry(customer_account, 'credit', str(amount_locked))
         tx.commit()
     except Exception as e:
         return jsonify({'status': 'error', 'message': f'accounting error: {str(e)}'}), 500
@@
     # create investment record in sqlite
     inv_id = None
     try:
-        inv_id = create_investment(user['id'], product_code, qty, str(price), str(amount_locked), terms_hash, agreement_signature)
+        # ensure user has wallet_code
+        wallet_code = user.get('wallet_code')
+        if not wallet_code:
+            wallet_code = f"116{user.get('id')[:8]}"
+            # persist wallet_code to user record
+            users = load_users()
+            for u in users:
+                if u.get('email') == email:
+                    u['wallet_code'] = wallet_code
+            save_users(users)
+
+        # cost_of_goods defaults to amount_locked unless provided
+        cost_of_goods = data.get('cost_of_goods') or str(amount_locked)
+        inv_id = create_investment(user['id'], wallet_code, product_code, qty, str(price), str(amount_locked), terms_hash, agreement_signature, cost_of_goods)
     except Exception as e:
         return jsonify({'status': 'error', 'message': f'investment creation failed: {str(e)}'}), 500
*** End Patch
