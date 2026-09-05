#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tenant-Specific Video Surveillance System
نظام المراقبة بالفيديو الخاص بكل مستأجر

FEATURE ISOLATION:
✅ Each tenant has ISOLATED video storage
✅ Only tenant managers/owners can access their videos
✅ Super Admin has ZERO visibility
✅ Videos linked to invoice IDs per tenant
"""

import uuid
import json
import os
from datetime import datetime
from typing import Dict, Optional, List
from tenancy_core import TenantContext, tenancy_manager

VIDEO_DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'video_logs.json')


class TenantVideoManager:
    """
    إدارة الفيديوهات الخاصة بكل مستأجر
    Manages video surveillance for individual tenants
    """
    
    def __init__(self):
        self.video_logs = self._load_video_logs()
    
    def _load_video_logs(self) -> Dict:
        """تحميل سجلات الفيديو"""
        if os.path.exists(VIDEO_DB_PATH):
            with open(VIDEO_DB_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def _save_video_logs(self):
        """حفظ سجلات الفيديو"""
        os.makedirs(os.path.dirname(VIDEO_DB_PATH), exist_ok=True)
        with open(VIDEO_DB_PATH, 'w', encoding='utf-8') as f:
            json.dump(self.video_logs, f, ensure_ascii=False, indent=2)
    
    def record_video_for_invoice(self, tenant_id: str, invoice_id: str, 
                                video_filename: str, duration_seconds: int,
                                camera_location: str = 'checkout_1') -> Dict:
        """
        تسجيل فيديو لفاتورة محددة
        Record video clip for specific invoice (tenant-isolated)
        
        Args:
            tenant_id: معرف المستأجر (MUST match current context)
            invoice_id: معرف الفاتورة
            video_filename: اسم ملف الفيديو
            duration_seconds: مدة الفيديو بالثواني
            camera_location: موقع الكاميرا
        """
        # SECURITY CHECK: Ensure tenant context matches
        if TenantContext.get_tenant() != tenant_id:
            raise PermissionError(f"❌ Tenant context mismatch! Expected {TenantContext.get_tenant()}, got {tenant_id}")
        
        # Verify tenant exists
        tenant = tenancy_manager.get_tenant(tenant_id)
        if not tenant:
            raise ValueError(f"❌ Tenant {tenant_id} not found")
        
        # Check if video surveillance is enabled for this tier
        if not tenant['features_enabled'].get('video_surveillance', False):
            raise PermissionError(f"❌ Video surveillance not enabled for tenant {tenant_id}")
        
        video_id = f"vid_{str(uuid.uuid4())[:8]}"
        
        # Construct isolated S3 path per tenant
        s3_path = f"{tenant['video_storage']}{datetime.now().year}/{invoice_id}/{video_filename}"
        
        video_record = {
            'video_id': video_id,
            'tenant_id': tenant_id,  # CRITICAL: Tenant isolation
            'invoice_id': invoice_id,
            'video_filename': video_filename,
            's3_path': s3_path,
            'duration_seconds': duration_seconds,
            'camera_location': camera_location,
            'recorded_at': datetime.utcnow().isoformat(),
            'file_size_mb': 0.0,  # Will be updated after upload
            'status': 'recorded'  # recorded, uploaded, archived, deleted
        }
        
        # Store in tenant-specific section
        if tenant_id not in self.video_logs:
            self.video_logs[tenant_id] = []
        
        self.video_logs[tenant_id].append(video_record)
        self._save_video_logs()
        
        return video_record
    
    def get_video_for_invoice(self, tenant_id: str, invoice_id: str,
                            user_email: str, user_role: str) -> Optional[Dict]:
        """
        احصل على فيديو لفاتورة محددة (مع تحقق من الصلاحيات)
        Retrieve video for invoice with STRICT tenant isolation
        
        SECURITY CHECKS:
        ✅ Only managers/owners of this tenant can access
        ✅ Super Admin is BLOCKED
        ✅ Video must belong to their tenant
        """
        # BLOCK Super Admin access
        if user_role == 'super_admin':
            raise PermissionError(
                "❌ COMPLIANCE VIOLATION: Super Admin cannot access tenant video surveillance. "
                "Videos are private to each business for regulatory compliance."
            )
        
        # Verify tenant ownership
        tenant = tenancy_manager.get_tenant(tenant_id)
        if not tenant:
            raise ValueError(f"❌ Tenant not found: {tenant_id}")
        
        # Check user permission level
        user_is_authorized = False
        for user in tenant['users']:
            if user['email'] == user_email and user['role'] in ['owner', 'manager']:
                user_is_authorized = True
                break
        
        if not user_is_authorized:
            raise PermissionError(
                f"❌ User {user_email} not authorized to access videos for tenant {tenant_id}"
            )
        
        # Retrieve video from tenant-specific storage only
        if tenant_id not in self.video_logs:
            return None
        
        for video in self.video_logs[tenant_id]:
            if video['invoice_id'] == invoice_id:
                return video
        
        return None
    
    def list_tenant_videos(self, tenant_id: str, user_email: str, 
                          user_role: str, limit: int = 100) -> List[Dict]:
        """
        احصل على قائمة الفيديوهات الخاصة بالمستأجر فقط
        List videos for this tenant only
        """
        # BLOCK Super Admin
        if user_role == 'super_admin':
            return []  # Empty list - no access
        
        # Verify tenant authorization
        tenant = tenancy_manager.get_tenant(tenant_id)
        if not tenant:
            return []
        
        user_is_authorized = False
        for user in tenant['users']:
            if user['email'] == user_email and user['role'] in ['owner', 'manager']:
                user_is_authorized = True
                break
        
        if not user_is_authorized:
            return []
        
        # Return only videos from this tenant
        videos = self.video_logs.get(tenant_id, [])
        return videos[-limit:] if len(videos) > limit else videos
    
    def delete_video_for_tenant(self, tenant_id: str, video_id: str,
                               user_email: str, user_role: str) -> bool:
        """
        حذف فيديو (مع تحقق من الصلاحيات)
        Delete video with authorization check
        """
        # BLOCK Super Admin
        if user_role == 'super_admin':
            raise PermissionError("❌ Super Admin cannot delete tenant videos")
        
        # Verify authorization
        tenant = tenancy_manager.get_tenant(tenant_id)
        if not tenant:
            return False
        
        user_is_authorized = any(
            user['email'] == user_email and user['role'] == 'owner'
            for user in tenant['users']
        )
        
        if not user_is_authorized:
            raise PermissionError("❌ Only tenant owner can delete videos")
        
        # Delete from tenant-specific storage
        if tenant_id not in self.video_logs:
            return False
        
        for i, video in enumerate(self.video_logs[tenant_id]):
            if video['video_id'] == video_id:
                video['status'] = 'deleted'
                video['deleted_at'] = datetime.utcnow().isoformat()
                self.video_logs[tenant_id][i] = video
                self._save_video_logs()
                return True
        
        return False


# Initialize Video Manager
video_manager = TenantVideoManager()
