#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Super Admin Dashboard Controller
لوحة التحكم للمسؤول الأعلى (النظام فقط)

RESPONSIBILITIES (نطاق المسؤولية):
✅ Subscription Management (تفعيل/إيقاف الشركات)
✅ System Feature Toggles (تفعيل/تعطيل الميزات حسب المستوى)
✅ Platform Revenue Reporting (الإيرادات من الاشتراكات)
❌ NO tenant inventory access
❌ NO tenant video access
❌ NO tenant accounting access
"""

import json
from typing import Dict, List
from datetime import datetime
from decimal import Decimal
from tenancy_core import tenancy_manager, TenantManager


class SuperAdminController:
    """
    Super Admin Controller - System-Level Operations Only
    """
    
    def __init__(self):
        self.manager = tenancy_manager
    
    def get_dashboard_metrics(self) -> Dict:
        """
        احصل على مقاييس لوحة التحكم (مستوى النظام فقط)
        Get system-level metrics only
        """
        tenants = self.manager.list_all_tenants()
        
        total_active = sum(1 for t in tenants if t['status'] == 'active')
        total_suspended = sum(1 for t in tenants if t['status'] == 'suspended')
        total_blocked = sum(1 for t in tenants if t['status'] == 'blocked')
        
        # Subscription breakdown
        tier_breakdown = {
            'free': sum(1 for t in tenants if t['subscription_tier'] == 'free'),
            'pro': sum(1 for t in tenants if t['subscription_tier'] == 'pro'),
            'enterprise': sum(1 for t in tenants if t['subscription_tier'] == 'enterprise')
        }
        
        # Platform revenue (dummy calculation - link to payment system)
        platform_revenue = self._calculate_platform_revenue()
        
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'total_tenants': len(tenants),
            'active_tenants': total_active,
            'suspended_tenants': total_suspended,
            'blocked_tenants': total_blocked,
            'subscription_breakdown': tier_breakdown,
            'platform_revenue': platform_revenue,
            'note': '🔒 This dashboard shows SYSTEM-LEVEL metrics only. Tenant operations are isolated.'
        }
    
    def _calculate_platform_revenue(self) -> Dict:
        """
        حساب إيرادات المنصة من الاشتراكات
        Calculate platform revenue from subscriptions
        """
        tenants = self.manager.list_all_tenants()
        
        pricing = {
            'free': Decimal('0'),
            'pro': Decimal('99.99'),
            'enterprise': Decimal('499.99')
        }
        
        monthly_revenue = sum(
            pricing.get(t['subscription_tier'], Decimal('0'))
            for t in tenants if t['status'] == 'active'
        )
        
        return {
            'monthly_revenue_usd': float(monthly_revenue),
            'monthly_revenue_sar': float(monthly_revenue * Decimal('3.75')),
            'currency': 'USD / SAR',
            'calculated_at': datetime.utcnow().isoformat()
        }
    
    def activate_subscription(self, tenant_id: str, tier: str) -> Dict:
        """
        تفعيل الاشتراك للشركة
        Activate subscription for a company
        """
        result = self.manager.update_subscription(tenant_id, tier)
        result_activate = self.manager.activate_tenant(tenant_id)
        
        if result and result_activate:
            tenant = self.manager.get_tenant(tenant_id)
            return {
                'status': 'success',
                'message': f'✅ Subscription activated for {tenant["business_name"]}',
                'tenant_id': tenant_id,
                'tier': tier,
                'features': tenant['features_enabled'],
                'timestamp': datetime.utcnow().isoformat()
            }
        
        return {'status': 'error', 'message': 'Failed to activate subscription'}
    
    def deactivate_subscription(self, tenant_id: str) -> Dict:
        """
        إيقاف الاشتراك للشركة
        Deactivate subscription for a company
        """
        result = self.manager.suspend_tenant(tenant_id, reason='Subscription deactivated by admin')
        
        if result:
            tenant = self.manager.get_tenant(tenant_id)
            return {
                'status': 'success',
                'message': f'⏸️ Subscription suspended for {tenant["business_name"]}',
                'tenant_id': tenant_id,
                'timestamp': datetime.utcnow().isoformat()
            }
        
        return {'status': 'error', 'message': 'Failed to deactivate subscription'}
    
    def block_company(self, tenant_id: str, reason: str) -> Dict:
        """
        حجب الشركة بشكل نهائي
        Permanently block a company
        """
        result = self.manager.block_tenant(tenant_id, reason=reason)
        
        if result:
            tenant = self.manager.get_tenant(tenant_id)
            return {
                'status': 'success',
                'message': f'🚫 Company {tenant["business_name"]} has been blocked',
                'tenant_id': tenant_id,
                'reason': reason,
                'timestamp': datetime.utcnow().isoformat()
            }
        
        return {'status': 'error', 'message': 'Failed to block company'}
    
    def enable_feature(self, tenant_id: str, feature_name: str) -> Dict:
        """
        تفعيل ميزة محددة للشركة
        Enable specific feature for a tenant
        """
        tenant = self.manager.get_tenant(tenant_id)
        if not tenant:
            return {'status': 'error', 'message': 'Tenant not found'}
        
        if feature_name not in tenant['features_enabled']:
            return {'status': 'error', 'message': 'Feature not found'}
        
        tenant['features_enabled'][feature_name] = True
        self.manager.tenants[tenant_id] = tenant
        self.manager._save_tenants()
        
        return {
            'status': 'success',
            'message': f'✅ Feature {feature_name} enabled for {tenant["business_name"]}',
            'tenant_id': tenant_id,
            'feature': feature_name
        }
    
    def disable_feature(self, tenant_id: str, feature_name: str) -> Dict:
        """
        تعطيل ميزة محددة للشركة
        Disable specific feature for a tenant
        """
        tenant = self.manager.get_tenant(tenant_id)
        if not tenant:
            return {'status': 'error', 'message': 'Tenant not found'}
        
        if feature_name not in tenant['features_enabled']:
            return {'status': 'error', 'message': 'Feature not found'}
        
        tenant['features_enabled'][feature_name] = False
        self.manager.tenants[tenant_id] = tenant
        self.manager._save_tenants()
        
        return {
            'status': 'success',
            'message': f'⛔ Feature {feature_name} disabled for {tenant["business_name"]}',
            'tenant_id': tenant_id,
            'feature': feature_name
        }
    
    def list_all_subscriptions(self) -> Dict:
        """
        احصل على قائمة بجميع الاشتراكات
        Get list of all subscriptions
        """
        tenants = self.manager.list_all_tenants()
        
        subscriptions = [
            {
                'tenant_id': t['tenant_id'],
                'business_name': t['business_name'],
                'owner_email': t['owner_email'],
                'tier': t['subscription_tier'],
                'status': t['status'],
                'created_at': t['created_at']
            }
            for t in tenants
        ]
        
        return {
            'total_subscriptions': len(subscriptions),
            'subscriptions': subscriptions,
            'timestamp': datetime.utcnow().isoformat()
        }


# Initialize Super Admin Controller
admin_controller = SuperAdminController()
