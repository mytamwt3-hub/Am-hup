#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tenancy Core - Multi-Tenant Architecture Foundation
إدارة النظام المتعدد المستأجرين (Multi-Tenancy)
"""

import uuid
import json
import os
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional

# Tenant Database Path
TENANT_DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'tenants.json')


class TenantManager:
    """
    إدارة المستأجرين (شركات العملاء)
    Manages individual business tenants on the platform
    """
    
    def __init__(self):
        self.tenants = self._load_tenants()
    
    def _load_tenants(self) -> Dict:
        """تحميل بيانات المستأجرين"""
        if os.path.exists(TENANT_DB_PATH):
            with open(TENANT_DB_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def _save_tenants(self):
        """حفظ بيانات المستأجرين"""
        os.makedirs(os.path.dirname(TENANT_DB_PATH), exist_ok=True)
        with open(TENANT_DB_PATH, 'w', encoding='utf-8') as f:
            json.dump(self.tenants, f, ensure_ascii=False, indent=2)
    
    def create_tenant(self, business_name: str, owner_email: str, subscription_tier: str) -> Dict:
        """
        إنشاء مستأجر جديد (شركة عميل جديدة)
        Create a new tenant (business)
        
        Args:
            business_name: اسم الشركة
            owner_email: بريد مالك الشركة
            subscription_tier: نوع الاشتراك (free, pro, enterprise)
        """
        tenant_id = f"tenant_{str(uuid.uuid4())[:8]}"
        
        tenant = {
            'tenant_id': tenant_id,
            'business_name': business_name,
            'owner_email': owner_email,
            'subscription_tier': subscription_tier,
            'status': 'active',  # active, suspended, blocked
            'features_enabled': self._get_features_for_tier(subscription_tier),
            'storage_bucket': f"s3://metahop-tenants/{tenant_id}/",
            'video_storage': f"s3://metahop-tenants/{tenant_id}/videos/",
            'ledger_year': datetime.now().year,
            'is_year_locked': False,
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat(),
            'users': [],
            'branches': []
        }
        
        self.tenants[tenant_id] = tenant
        self._save_tenants()
        return tenant
    
    def _get_features_for_tier(self, tier: str) -> Dict[str, bool]:
        """
        احصل على الميزات المتاحة لمستوى الاشتراك
        Returns features available for subscription tier
        """
        features = {
            'free': {
                'pos_system': True,
                'inventory': True,
                'accounting': False,
                'video_surveillance': False,
                'employee_management': False,
                'e_invoicing': False,
                'max_users': 1,
                'max_products': 50
            },
            'pro': {
                'pos_system': True,
                'inventory': True,
                'accounting': True,
                'video_surveillance': True,
                'employee_management': True,
                'e_invoicing': True,
                'max_users': 10,
                'max_products': 1000
            },
            'enterprise': {
                'pos_system': True,
                'inventory': True,
                'accounting': True,
                'video_surveillance': True,
                'employee_management': True,
                'e_invoicing': True,
                'max_users': 100,
                'max_products': 999999
            }
        }
        return features.get(tier, features['free'])
    
    def get_tenant(self, tenant_id: str) -> Optional[Dict]:
        """احصل على بيانات المستأجر"""
        return self.tenants.get(tenant_id)
    
    def update_subscription(self, tenant_id: str, new_tier: str) -> bool:
        """
        تحديث مستوى الاشتراك للمستأجر
        Update tenant subscription tier
        """
        if tenant_id not in self.tenants:
            return False
        
        self.tenants[tenant_id]['subscription_tier'] = new_tier
        self.tenants[tenant_id]['features_enabled'] = self._get_features_for_tier(new_tier)
        self.tenants[tenant_id]['updated_at'] = datetime.utcnow().isoformat()
        self._save_tenants()
        return True
    
    def suspend_tenant(self, tenant_id: str, reason: str = '') -> bool:
        """إيقاف المستأجر مؤقتاً"""
        if tenant_id not in self.tenants:
            return False
        
        self.tenants[tenant_id]['status'] = 'suspended'
        self.tenants[tenant_id]['suspension_reason'] = reason
        self.tenants[tenant_id]['updated_at'] = datetime.utcnow().isoformat()
        self._save_tenants()
        return True
    
    def block_tenant(self, tenant_id: str, reason: str = '') -> bool:
        """حجب المستأجر بشكل نهائي"""
        if tenant_id not in self.tenants:
            return False
        
        self.tenants[tenant_id]['status'] = 'blocked'
        self.tenants[tenant_id]['block_reason'] = reason
        self.tenants[tenant_id]['updated_at'] = datetime.utcnow().isoformat()
        self._save_tenants()
        return True
    
    def activate_tenant(self, tenant_id: str) -> bool:
        """تفعيل المستأجر"""
        if tenant_id not in self.tenants:
            return False
        
        self.tenants[tenant_id]['status'] = 'active'
        self.tenants[tenant_id]['updated_at'] = datetime.utcnow().isoformat()
        self._save_tenants()
        return True
    
    def lock_tenant_year(self, tenant_id: str) -> bool:
        """
        قفل السنة المالية للمستأجر (إغلاق السنة)
        Lock fiscal year for this tenant only
        """
        if tenant_id not in self.tenants:
            return False
        
        self.tenants[tenant_id]['is_year_locked'] = True
        self.tenants[tenant_id]['locked_year'] = datetime.now().year
        self.tenants[tenant_id]['year_locked_at'] = datetime.utcnow().isoformat()
        self._save_tenants()
        return True
    
    def reset_tenant_year(self, tenant_id: str) -> bool:
        """
        إعادة تعيين السنة المالية للمستأجر (للسنة الجديدة)
        Reset fiscal year for this tenant only
        """
        if tenant_id not in self.tenants:
            return False
        
        current_year = datetime.now().year
        self.tenants[tenant_id]['ledger_year'] = current_year
        self.tenants[tenant_id]['is_year_locked'] = False
        self.tenants[tenant_id]['updated_at'] = datetime.utcnow().isoformat()
        self._save_tenants()
        return True
    
    def list_all_tenants(self) -> List[Dict]:
        """احصل على قائمة بجميع المستأجرين"""
        return list(self.tenants.values())
    
    def add_user_to_tenant(self, tenant_id: str, user_email: str, role: str) -> bool:
        """
        إضافة مستخدم للمستأجر
        role: 'owner', 'manager', 'employee'
        """
        if tenant_id not in self.tenants:
            return False
        
        user = {
            'email': user_email,
            'role': role,
            'added_at': datetime.utcnow().isoformat()
        }
        self.tenants[tenant_id]['users'].append(user)
        self._save_tenants()
        return True


class TenantContext:
    """
    سياق المستأجر الحالي (Current Tenant Context)
    Tracks the current tenant context for isolated operations
    """
    
    _current_tenant_id = None
    
    @classmethod
    def set_tenant(cls, tenant_id: str):
        """تعيين المستأجر الحالي"""
        cls._current_tenant_id = tenant_id
    
    @classmethod
    def get_tenant(cls) -> Optional[str]:
        """الحصول على المستأجر الحالي"""
        return cls._current_tenant_id
    
    @classmethod
    def clear_tenant(cls):
        """مسح سياق المستأجر"""
        cls._current_tenant_id = None


# Initialize Tenant Manager
tenancy_manager = TenantManager()
