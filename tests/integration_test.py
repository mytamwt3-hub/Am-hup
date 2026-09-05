@@
 # Prepare test investor
 owner_id = 'test-investor-1'
 user_email = 'investor1@example.local'
+wallet_code = '116testinv1'
@@
 print('\nCreating investment record in sqlite...')
-inv_id = create_investment(owner_id, 'P_TEST', total_qty, str(unit_price), str(amount_locked), 'terms_hash_example', 'agreement_sig_example')
+inv_id = create_investment(owner_id, wallet_code, 'P_TEST', total_qty, str(unit_price), str(amount_locked), 'terms_hash_example', 'agreement_sig_example')
 print('Created investment', inv_id)
*** End Patch
