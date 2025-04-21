"""
Message handler for WebSocket messages.

@author Bruno Santos
"""

import json
import asyncio
from typing import Dict, Any, Callable, Awaitable
from ..utils.logger import logger
from .client import WhatsAppGatewayClient

class WebSocketMessageHandler:
    """Handler for WebSocket messages."""
    
    def __init__(self, gateway_client: WhatsAppGatewayClient):
        """Initialize the message handler."""
        self.gateway_client = gateway_client
        self.command_handlers: Dict[str, Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]]] = {}
        
        # Register event handlers
        self._register_event_handlers()
    
    def register_command_handler(
        self, 
        command: str, 
        handler: Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]]
    ) -> None:
        """Register a handler for a specific command."""
        self.command_handlers[command] = handler
    
    async def handle_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle a message from Claude Desktop."""
        try:
            # Validate message format
            if "command" not in message:
                return self._create_error_response("Missing command field")
            
            command = message.get("command")
            
            # Check if command is registered
            if command not in self.command_handlers:
                return self._create_error_response(f"Unknown command: {command}")
            
            # Call command handler
            return await self.command_handlers[command](message)
        except Exception as e:
            logger.exception(f"Error handling message: {e}")
            return self._create_error_response(f"Error processing command: {str(e)}")
    
    def _create_error_response(self, error_message: str) -> Dict[str, Any]:
        """Create an error response."""
        return {
            "success": False,
            "error": error_message,
        }
    
    def _register_event_handlers(self) -> None:
        """Register event handlers for WhatsApp Gateway events."""
        # QR code event
        self.gateway_client.register_event_handler("qr", self._handle_qr_event)
        
        # Ready event
        self.gateway_client.register_event_handler("ready", self._handle_ready_event)
        
        # Message event
        self.gateway_client.register_event_handler("message", self._handle_message_event)
        
        # Disconnected event
        self.gateway_client.register_event_handler("disconnected", self._handle_disconnected_event)
    
    async def _handle_qr_event(self, data: Dict[str, Any]) -> None:
        """Handle QR code event."""
        logger.info("Received QR code for WhatsApp authentication")
        # This event will be forwarded to Claude Desktop by the MCP handler
    
    async def _handle_ready_event(self, data: Dict[str, Any]) -> None:
        """Handle ready event."""
        logger.info("WhatsApp Gateway is ready")
        # This event will be forwarded to Claude Desktop by the MCP handler
    
    async def _handle_message_event(self, data: Dict[str, Any]) -> None:
        """Handle message event."""
        message = data.get("message", {})
        logger.debug(f"Received WhatsApp message: {message.get('id')}")
        # This event will be forwarded to Claude Desktop by the MCP handler
    
    async def _handle_disconnected_event(self, data: Dict[str, Any]) -> None:
        """Handle disconnected event."""
        reason = data.get("reason", "Unknown reason")
        logger.warning(f"WhatsApp disconnected: {reason}")
        # This event will be forwarded to Claude Desktop by the MCP handler
