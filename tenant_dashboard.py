#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tenant/Business Dashboard Controller
لوحة تحكم المستأجر (الشركة العميل)

RESPONSIBILITIES (نطاق المسؤولية):
✅ POS System (نظام نقاط البيع)
✅ Inventory Management (إدارة المخزون)
✅ Accounting/Ledger (المحاسبة)
✅ Employee Management (إدارة الموظفين)
✅ Video Surveillance (المراقبة - خاص بهم فقط)
✅ Year-End Closing (إغلاق السنة - خاص بهم فقط)
"""

from typing import Dict, List, Optional
from datetime import datetime
from tenancy_core import TenantContext, tenancy_manager
from video_security_tenant import video_manager


class TenantDashboardController:
    """
    Tenant Dashboard - Operational Control for Business
    """
    
    def __init__(self):
        self.tenant_manager = tenancy_manager
        self.video_manager = video_manager
    
    def _verify_tenant_access(self, tenant_id: str, user_email: str, 
                             required_role: str = 'manager') -> bool:
        """
        التحقق من صلاحية المستخدم للوصول للمستأجر
        Verify user has access to tenant
        """
        tenant = self.tenant_manager.get_tenant(tenant_id)
        if not tenant:
            return False
        
        for user in tenant['users']:
            if user['email'] == user_email and user['role'] in [required_role, 'owner']:
                return True
        
        return False
    
    def get_business_dashboard_metrics(self, tenant_id: str, user_email: str) -> Dict:
        """
        احصل على مقاييس لوحة التحكم التشغيلية للشركة
        Get operational metrics for business
        """
        if not self._verify_tenant_access(tenant_id, user_email):
            return {'status': 'error', 'message': 'Access denied'}
        
        TenantContext.set_tenant(tenant_id)
        tenant = self.tenant_manager.get_tenant(tenant_id)
        
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'tenant_id': tenant_id,
            'business_name': tenant['business_name'],
            'subscription_tier': tenant['subscription_tier'],
            'features_enabled': tenant['features_enabled'],
            'ledger_year': tenant['ledger_year'],
            'is_year_locked': tenant['is_year_locked'],
            'note': '🔐 This dashboard is isolated to your business only. No cross-tenant access.'
        }
    
    def access_video_surveillance(self, tenant_id: str, user_email: str,
                                 invoice_id: str) -> Optional[Dict]:
        """
        الوصول لفيديوهات المراقبة (معزول تماماً للشركة)
        Access video surveillance for invoice audit
        """
        if not self._verify_tenant_access(tenant_id, user_email, required_role='manager'):
            return {'status': 'error', 'message': 'Access denied'}
        
        TenantContext.set_tenant(tenant_id)
        
        try:
            video = self.video_manager.get_video_for_invoice(
                tenant_id, invoice_id, user_email, 'manager'
            )
            if not video:
                return {'status': 'not_found', 'message': 'No video found for this invoice'}
            
            return {
                'status': 'success',
                'video': video,
                'access_level': 'manager',
                'timestamp': datetime.utcnow().isoformat()
            }
        except PermissionError as e:
            return {'status': 'error', 'message': str(e)}
    
    def list_checkout_videos(self, tenant_id: str, user_email: str) -> Dict:
        """
        احصل على قائمة فيديوهات الكاشير (خاص بالشركة فقط)
        List all checkout videos for this tenant
        """
        if not self._verify_tenant_access(tenant_id, user_email, required_role='manager'):
            return {'status': 'error', 'message': 'Access denied'}
        
        TenantContext.set_tenant(tenant_id)
        tenant = self.tenant_manager.get_tenant(tenant_id)
        
        if not tenant['features_enabled'].get('video_surveillance', False):
            return {'status': 'error', 'message': 'Video surveillance not enabled for your plan'}
        
        videos = self.video_manager.list_tenant_videos(
            tenant_id, user_email, 'manager', limit=50
        )
        
        return {
            'status': 'success',
            'tenant_id': tenant_id,
            'total_videos': len(videos),
            'videos': videos,
            'isolated_to_tenant': True,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def lock_fiscal_year(self, tenant_id: str, user_email: str) -> Dict:
        """
        قفل السنة المالية لهذا المستأجر ONLY
        Lock fiscal year for THIS TENANT ONLY
        
        CRITICAL:
        ✅ This only locks THIS tenant's ledger
        ✅ Does NOT affect other tenants
        ✅ Other businesses can continue operations
        """
        # Only owner can lock year
        if not self._verify_tenant_access(tenant_id, user_email, required_role='owner'):
            return {'status': 'error', 'message': 'Only business owner can lock fiscal year'}
        
        TenantContext.set_tenant(tenant_id)
        tenant = self.tenant_manager.get_tenant(tenant_id)
        
        if tenant['is_year_locked']:
            return {
                'status': 'warning',
                'message': f'Fiscal year {tenant["locked_year"]} is already locked',
                'locked_at': tenant.get('year_locked_at')
            }
        
        # Lock ONLY this tenant's year
        result = self.tenant_manager.lock_tenant_year(tenant_id)
        
        if result:
            return {
                'status': 'success',
                'message': f'✅ Fiscal year {datetime.now().year} locked for {tenant["business_name"]}',
                'tenant_id': tenant_id,
                'business_name': tenant['business_name'],
                'locked_year': datetime.now().year,
                'note': '🔒 Only this business is affected. Other companies continue normally.',
                'timestamp': datetime.utcnow().isoformat()
            }
        
        return {'status': 'error', 'message': 'Failed to lock fiscal year'}
    
    def reset_fiscal_year(self, tenant_id: str, user_email: str) -> Dict:
        """
        إعادة تعيين السنة المالية للمستأجر (للسنة الجديدة)
        Reset fiscal year for NEW year (THIS TENANT ONLY)
        """
        # Only owner can reset year
        if not self._verify_tenant_access(tenant_id, user_email, required_role='owner'):
            return {'status': 'error', 'message': 'Only business owner can reset fiscal year'}
        
        TenantContext.set_tenant(tenant_id)
        tenant = self.tenant_manager.get_tenant(tenant_id)
        
        # Reset ONLY this tenant's year
        result = self.tenant_manager.reset_tenant_year(tenant_id)
        
        if result:
            updated_tenant = self.tenant_manager.get_tenant(tenant_id)
            return {
                'status': 'success',
                'message': f'✅ Fiscal year reset to {updated_tenant["ledger_year"]} for {tenant["business_name"]}',
                'tenant_id': tenant_id,
                'business_name': tenant['business_name'],
                'new_year': updated_tenant['ledger_year'],
                'note': '🔄 New fiscal year started for this business only.',
                'timestamp': datetime.utcnow().isoformat()
            }
        
        return {'status': 'error', 'message': 'Failed to reset fiscal year'}
    
    def get_year_status(self, tenant_id: str, user_email: str) -> Dict:
        """
        احصل على حالة السنة المالية للمستأجر
        Get fiscal year status for tenant
        """
        if not self._verify_tenant_access(tenant_id, user_email):
            return {'status': 'error', 'message': 'Access denied'}
        
        TenantContext.set_tenant(tenant_id)
        tenant = self.tenant_manager.get_tenant(tenant_id)
        
        return {
            'status': 'success',
            'tenant_id': tenant_id,
            'business_name': tenant['business_name'],
            'current_year': tenant['ledger_year'],
            'is_locked': tenant['is_year_locked'],
            'locked_year': tenant.get('locked_year'),
            'locked_at': tenant.get('year_locked_at'),
            'isolated_to_tenant': True
        }


# Initialize Tenant Dashboard Controller
tenant_controller = TenantDashboardController()
