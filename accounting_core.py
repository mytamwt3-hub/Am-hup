@@
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
-        alloc_fee = platform_fee * (allocate_qty / qty) if qty else 0.0
+        alloc_fee = platform_fee * (allocate_qty / qty) if qty else 0.0
         # update inv sales and remaining
-        new_rem = rem - allocate_qty
-        update_investment_remaining(inv_id, new_rem, alloc_amount)
+        new_rem = rem - allocate_qty
+        update_investment_remaining(inv_id, new_rem, alloc_amount, alloc_fee)
         remaining_to_allocate -= allocate_qty
         # if investment depleted -> close
         if new_rem == 0:
             close_investment(inv_id)
 
     return True
@@
 def buyFromStore(product_code: str, quantity: int, customer_account: Account, sales_account: Account, 
                  customer_phone: str = None, inventory_station: str = '121') -> Dict:
@@
     # عمولة المنصة 5%
     platform = ACCOUNTS.get('417') or Account('417', 'عمولة_المنصة', nature='credit')
     platform_fee = (total * Decimal('0.05')).quantize(CENT, rounding=ROUND_HALF_EVEN)
     fee_tx = Transaction(description=f"عمولة منصة على بيع {product_code}: {platform_fee}")
     fee_tx.add_entry(sales_account, 'debit', platform_fee)
     fee_tx.add_entry(platform, 'credit', platform_fee)
     fee_tx.commit()
@@
     # حفظ الطلب
     order = {
         'invoice_id': invoice_id,
         'product': product_code,
         'quantity': int(quantity),
-        'total': decimal_to_str(total),
-        'platform_fee': decimal_to_str(platform_fee),
+        'total': decimal_to_str(total),
+        'platform_fee': decimal_to_str(platform_fee),
         'status': 'delivered',
         'created_at': now.isoformat(),
         'customer_phone': customer_phone
     }
@@
     try:
-        from investments import allocate_sale_for_order
-        allocate_sale_for_order(order)
+        from investments import allocate_sale_for_order
+        allocate_sale_for_order(order)
     except Exception:
         pass
*** End Patch
