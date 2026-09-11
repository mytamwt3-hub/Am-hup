from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status, Query, Depends
from sqlalchemy.orm import Session
from core.security import verify_token
from core.models import Tenant
from config.database import SessionLocal
import json
import logging
from typing import Dict, Set

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ws", tags=["websocket"])

# Store active connections per tenant
active_connections: Dict[str, Set[WebSocket]] = {}


class ConnectionManager:
    """Manage WebSocket connections per tenant"""
    
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, tenant_id: str, websocket: WebSocket):
        await websocket.accept()
        if tenant_id not in self.active_connections:
            self.active_connections[tenant_id] = set()
        self.active_connections[tenant_id].add(websocket)
        logger.info(f"✅ WebSocket connected for tenant: {tenant_id}")
    
    def disconnect(self, tenant_id: str, websocket: WebSocket):
        if tenant_id in self.active_connections:
            self.active_connections[tenant_id].discard(websocket)
            if not self.active_connections[tenant_id]:
                del self.active_connections[tenant_id]
        logger.info(f"❌ WebSocket disconnected for tenant: {tenant_id}")
    
    async def broadcast_to_tenant(self, tenant_id: str, message: dict):
        """Broadcast message to all connected clients in a tenant"""
        if tenant_id in self.active_connections:
            for connection in list(self.active_connections[tenant_id]):
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending message: {str(e)}")
                    self.active_connections[tenant_id].discard(connection)
    
    async def send_to_specific(self, websocket: WebSocket, message: dict):
        """Send message to specific connection"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending specific message: {str(e)}")


manager = ConnectionManager()


@router.websocket("/notifications")
async def websocket_notifications(websocket: WebSocket, token: str = Query(...)):
    """
    WebSocket endpoint for real-time notifications
    Requires valid JWT token in query string
    
    Usage: ws://localhost:8000/api/v1/ws/notifications?token=<jwt_token>
    """
    try:
        # Verify token
        payload = verify_token(token)
        tenant_id = payload.get("tenant_id")
        user_id = payload.get("sub")
        
        if not tenant_id:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        
        # Connect to tenant's notification channel
        await manager.connect(tenant_id, websocket)
        
        # Send welcome message
        await manager.send_to_specific(websocket, {
            "type": "connection_established",
            "tenant_id": tenant_id,
            "user_id": user_id,
            "message": "Connected to notifications channel"
        })
        
        # Listen for messages
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle heartbeat
            if message.get("type") == "ping":
                await manager.send_to_specific(websocket, {"type": "pong"})
            
            # Log received message
            logger.debug(f"Message from {tenant_id}: {message}")
    
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
    
    finally:
        manager.disconnect(tenant_id, websocket)


# Helper function to notify all users of a tenant
async def notify_tenant(tenant_id: str, event_type: str, data: dict):
    """
    Notify all connected clients of a tenant about an event
    
    Example: Establishment approval notification
    """
    message = {
        "type": event_type,
        "data": data,
        "timestamp": str(__import__('datetime').datetime.utcnow())
    }
    await manager.broadcast_to_tenant(tenant_id, message)
