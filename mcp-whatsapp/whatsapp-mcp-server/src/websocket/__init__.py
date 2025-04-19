"""
WebSocket module initialization.
Contains classes for WebSocket client and message handling.

@author Bruno Santos
"""

from .client import WhatsAppGatewayClient
from .message_handler import WebSocketMessageHandler

__all__ = ['WhatsAppGatewayClient', 'WebSocketMessageHandler']