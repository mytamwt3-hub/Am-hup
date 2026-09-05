#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Refactored Backend Server - Tenant-Aware API
خادم النهاية الخلفية المعاد هيكلته مع دعم المستأجرين

CRITICAL FEATURES:
✅ All endpoints are tenant-scoped
✅ Video endpoints link to tenant storage only
✅ Accounting operations isolated per tenant
✅ Super Admin API routes separate from tenant routes
✅ Year-end closing restricted to tenant owners
"""

from flask import Flask, request, jsonify
from functools import wraps
from typing import Dict, Optional
from datetime import datetime
from decimal import Decimal

from tenancy_core import TenantContext, tenancy_manager
from video_security_tenant import video_manager
from accounting_system_tenant import accounting_system, TenantTransaction, TenantAccount
from year_end_closing_tenant import year_closing_system
from admin_dashboard import admin_controller
from tenant_dashboard import tenant_controller

app = Flask(__name__)


def verify_tenant_context(f):
    """
    تأكيد أن المستخدم لديه سياق شركة صالح
    Decorator: Verify tenant context is set
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        tenant_id = request.headers.get('X-Tenant-ID')
        user_email = request.headers.get('X-User-Email')
        user_role = request.headers.get('X-User-Role')
        
        if not tenant_id or not user_email or not user_role:
            return jsonify({
                'status': 'error',
                'message': '❌ Missing required headers: X-Tenant-ID, X-User-Email, X-User-Role'
            }), 400
        
        TenantContext.set_tenant(tenant_id)
        return f(*args, tenant_id=tenant_id, user_email=user_email, user_role=user_role, **kwargs)
    
    return decorated_function


# ============================================================================
# SUPER ADMIN ROUTES (System-Level Only)
# ============================================================================

@app.route('/api/admin/dashboard', methods=['GET'])
@verify_tenant_context
def get_admin_dashboard(**context):
    """
    لوحة تحكم المشرف الرئيسي - مقاييس النظام فقط
    Super Admin Dashboard
    """
    if context['user_role'] != 'super_admin':
        return jsonify({'status': 'error', 'message': '❌ Super Admin access required'}), 403
    
    metrics = admin_controller.get_dashboard_metrics()
    return jsonify(metrics), 200


@app.route('/api/admin/subscriptions/activate', methods=['POST'])
@verify_tenant_context
def activate_subscription(**context):
    """
    تفعيل الاشتراك لشركة
    Activate subscription
    """
    if context['user_role'] != 'super_admin':
        return jsonify({'status': 'error', 'message': '❌ Super Admin access required'}), 403
    
    data = request.get_json()
    tenant_id = data.get('tenant_id')
    tier = data.get('tier')
    
    result = admin_controller.activate_subscription(tenant_id, tier)
    return jsonify(result), 200 if result['status'] == 'success' else 400


@app.route('/api/admin/subscriptions/deactivate', methods=['POST'])
@verify_tenant_context
def deactivate_subscription(**context):
    """
    إيقاف الاشتراك لشركة
    Deactivate subscription
    """
    if context['user_role'] != 'super_admin':
        return jsonify({'status': 'error', 'message': '❌ Super Admin access required'}), 403
    
    data = request.get_json()
    tenant_id = data.get('tenant_id')
    
    result = admin_controller.deactivate_subscription(tenant_id)
    return jsonify(result), 200 if result['status'] == 'success' else 400


@app.route('/api/admin/company/block', methods=['POST'])
@verify_tenant_context
def block_company(**context):
    """
    حجب شركة
    Block company
    """
    if context['user_role'] != 'super_admin':
        return jsonify({'status': 'error', 'message': '❌ Super Admin access required'}), 403
    
    data = request.get_json()
    tenant_id = data.get('tenant_id')
    reason = data.get('reason', '')
    
    result = admin_controller.block_company(tenant_id, reason)
    return jsonify(result), 200 if result['status'] == 'success' else 400


# ============================================================================
# TENANT ROUTES (Business Operations - Tenant Isolated)
# ============================================================================

@app.route('/api/tenant/dashboard', methods=['GET'])
@verify_tenant_context
def get_tenant_dashboard(tenant_id: str, user_email: str, **context):
    """
    لوحة تحكم الشركة - عمليات تشغيلية
    Tenant dashboard
    """
    metrics = tenant_controller.get_business_dashboard_metrics(tenant_id, user_email)
    return jsonify(metrics), 200 if metrics.get('status') != 'error' else 400


# ============================================================================
# VIDEO SURVEILLANCE ROUTES (Tenant-Isolated)
# ============================================================================

@app.route('/api/tenant/video/search-by-invoice', methods=['GET'])
@verify_tenant_context
def search_video_by_invoice(tenant_id: str, user_email: str, user_role: str, **context):
    """
    البحث عن فيديو برقم الفاتورة (معزول للشركة)
    Search video by invoice ID
    
    🔒 CRITICAL SECURITY:
    - Only tenant managers/owners can access
    - Super Admin gets BLOCKED
    - Video is tied to tenant's isolated storage
    """
    invoice_id = request.args.get('invoice_id')
    
    if not invoice_id:
        return jsonify({'status': 'error', 'message': 'Missing invoice_id parameter'}), 400
    
    try:
        # This will raise PermissionError if Super Admin tries to access
        video = video_manager.get_video_for_invoice(
            tenant_id, invoice_id, user_email, user_role
        )
        
        if not video:
            return jsonify({
                'status': 'not_found',
                'message': f'No video found for invoice {invoice_id}'
            }), 404
        
        return jsonify({
            'status': 'success',
            'video': video,
            'tenant_id': tenant_id,
            'isolated_access': True,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
    
    except PermissionError as e:
        return jsonify({
            'status': 'error',
            'message': str(e),
            'compliance_reason': 'Videos are private to each business for regulatory compliance'
        }), 403


@app.route('/api/tenant/video/list', methods=['GET'])
@verify_tenant_context
def list_tenant_videos(tenant_id: str, user_email: str, user_role: str, **context):
    """
    قائمة بفيديوهات الشركة (معزولة تماماً)
    List tenant videos
    """
    limit = request.args.get('limit', default=50, type=int)
    
    try:
        videos_result = video_manager.list_tenant_videos(
            tenant_id, user_email, user_role, limit=limit
        )
        
        return jsonify({
            'status': 'success',
            'videos': videos_result,
            'tenant_id': tenant_id,
            'isolated_to_tenant': True,
            'total_videos': len(videos_result),
            'timestamp': datetime.utcnow().isoformat()
        }), 200
    
    except PermissionError as e:
        return jsonify({'status': 'error', 'message': str(e)}), 403


@app.route('/api/tenant/video/record', methods=['POST'])
@verify_tenant_context
def record_video(tenant_id: str, user_email: str, **context):
    """
    تسجيل فيديو جديد (معزول للشركة)
    Record new video
    """
    data = request.get_json()
    invoice_id = data.get('invoice_id')
    video_filename = data.get('video_filename')
    duration_seconds = data.get('duration_seconds')
    camera_location = data.get('camera_location', 'checkout_1')
    
    try:
        TenantContext.set_tenant(tenant_id)
        video = video_manager.record_video_for_invoice(
            tenant_id, invoice_id, video_filename, duration_seconds, camera_location
        )
        
        return jsonify({
            'status': 'success',
            'video': video,
            'tenant_id': tenant_id,
            'storage': f's3://metahop-tenants/{tenant_id}/videos/',
            'timestamp': datetime.utcnow().isoformat()
        }), 201
    
    except (ValueError, PermissionError) as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400


# ============================================================================
# ACCOUNTING ROUTES (Tenant-Isolated Ledger)
# ============================================================================

@app.route('/api/tenant/accounting/record-sale', methods=['POST'])
@verify_tenant_context
def record_pos_sale(tenant_id: str, user_email: str, **context):
    """
    تسجيل عملية بيع من الكاشير مع ربطها برقم الفيديو
    Record POS sale with video link
    """
    data = request.get_json()
    invoice_id = data.get('invoice_id')
    video_id = data.get('video_id')
    amount = Decimal(str(data.get('amount', '0')))
    camera_location = data.get('camera_location', 'checkout_1')
    
    try:
        TenantContext.set_tenant(tenant_id)
        result = accounting_system.record_checkout_sale_with_video(
            tenant_id, invoice_id, video_id, amount, camera_location
        )
        
        status_code = 201 if result.get('status') == 'success' else 400
        return jsonify(result), status_code
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/tenant/accounting/trial-balance', methods=['GET'])
@verify_tenant_context
def get_trial_balance(tenant_id: str, user_email: str, **context):
    """
    ميزان المراجعة (معزول للشركة)
    Trial balance
    """
    try:
        TenantContext.set_tenant(tenant_id)
        result = accounting_system.get_trial_balance(tenant_id)
        return jsonify(result), 200
    except PermissionError:
        return jsonify({
            'status': 'error',
            'message': '❌ Cannot access other tenant\'s accounting data'
        }), 403


@app.route('/api/tenant/accounting/invoices-with-videos', methods=['GET'])
@verify_tenant_context
def get_invoices_with_videos(tenant_id: str, user_email: str, **context):
    """
    الفواتير المرتبطة برقم الفيديو (معزولة للشركة)
    Invoices linked to surveillance videos
    
    🔒 Super Admin gets EMPTY result
    ✅ Tenant managers/owners see all their invoices
    """
    try:
        TenantContext.set_tenant(tenant_id)
        result = accounting_system.get_invoices_with_videos(tenant_id)
        return jsonify(result), 200
    except PermissionError:
        return jsonify({
            'status': 'error',
            'message': '❌ Access denied. Videos are private to each business.'
        }), 403


# ============================================================================
# YEAR-END CLOSING ROUTES (Tenant Owner Only)
# ============================================================================

@app.route('/api/tenant/accounting/year-closing/prepare', methods=['GET'])
@verify_tenant_context
def prepare_year_closing(tenant_id: str, user_email: str, **context):
    """
    تحضير إغلاق السنة - معزول للشركة
    Prepare year-end closing
    """
    result = year_closing_system.prepare_closing(tenant_id, user_email)
    return jsonify(result), 200 if result.get('status') == 'success' else 400


@app.route('/api/tenant/accounting/year-closing/execute', methods=['POST'])
@verify_tenant_context
def execute_year_closing(tenant_id: str, user_email: str, user_role: str, **context):
    """
    تنفيذ إغلاق السنة (شركة واحدة فقط)
    Execute year-end closing
    
    🔒 CRITICAL:
    ❌ Super Admin BLOCKED
    ✅ Only tenant owner can execute
    ✅ Affects ONLY this tenant's ledger
    """
    data = request.get_json() or {}
    closing_notes = data.get('closing_notes', '')
    
    try:
        result = year_closing_system.execute_year_closing(
            tenant_id, user_email, user_role, closing_notes
        )
        
        status_code = 200 if result.get('status') == 'success' else 400
        return jsonify(result), status_code
    
    except (PermissionError, ValueError) as e:
        return jsonify({'status': 'error', 'message': str(e)}), 403


@app.route('/api/tenant/accounting/year-closing/history', methods=['GET'])
@verify_tenant_context
def get_closing_history(tenant_id: str, user_email: str, **context):
    """
    سجل الإغلاقات (معزول للشركة)
    Closing history
    """
    result = year_closing_system.get_closing_history(tenant_id)
    return jsonify(result), 200


# ============================================================================
# AUDIT & COMPLIANCE
# ============================================================================

@app.route('/api/audit/verify-isolation/<excluded_tenant_id>', methods=['GET'])
@verify_tenant_context
def verify_tenant_isolation(excluded_tenant_id: str, user_role: str, **context):
    """
    التحقق من عدم تأثر الشركات الأخرى
    Security audit - verify no cross-tenant impact
    """
    if user_role != 'super_admin':
        return jsonify({
            'status': 'error',
            'message': 'Audit endpoint requires Super Admin access'
        }), 403
    
    result = year_closing_system.verify_no_cross_tenant_impact(excluded_tenant_id)
    return jsonify(result), 200


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
