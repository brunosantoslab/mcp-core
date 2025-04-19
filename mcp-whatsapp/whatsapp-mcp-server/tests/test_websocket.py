"""
Tests for WebSocket client.

@author Bruno Santos
"""

import os
import json
import asyncio
import pytest
import websockets
from unittest.mock import MagicMock, patch

from src.websocket.client import WhatsAppGatewayClient

# Setup test fixtures
@pytest.fixture
def mock_websocket():
    """Create a mock WebSocket."""
    ws = MagicMock(spec=websockets.WebSocketClientProtocol)
    
    async def mock_send(data):
        """Mock send method."""
        return None
    
    async def mock_close():
        """Mock close method."""
        return None
    
    ws.send = mock_send
    ws.close = mock_close
    
    return ws

# Test cases
@pytest.mark.asyncio
async def test_connect(mock_websocket):
    """Test connecting to the WebSocket server."""
    with patch('websockets.connect', return_value=mock_websocket):
        client = WhatsAppGatewayClient("ws://localhost:8090/ws")
        result = await client.connect()
        
        assert result is True
        assert client.is_connected() is True

@pytest.mark.asyncio
async def test_disconnect(mock_websocket):
    """Test disconnecting from the WebSocket server."""
    with patch('websockets.connect', return_value=mock_websocket):
        client = WhatsAppGatewayClient("ws://localhost:8090/ws")
        await client.connect()
        await client.disconnect()
        
        assert client.is_connected() is False

@pytest.mark.asyncio
async def test_send_command(mock_websocket):
    """Test sending a command to the WebSocket server."""
    # Setup mock to return a response for the command
    async def mock_listen():
        return json.dumps({
            "type": "response",
            "id": "test_id",
            "command": "testCommand",
            "data": {"result": "success"},
            "timestamp": "2023-01-01T00:00:00Z",
        })
    
    mock_websocket.__aiter__.return_value = [mock_listen()]
    
    with patch('websockets.connect', return_value=mock_websocket):
        client = WhatsAppGatewayClient("ws://localhost:8090/ws")
        await client.connect()
        
        # Patch the receive_messages method to simulate a response
        async def mock_receive():
            # Get the pending command future
            future = list(client.pending_commands.values())[0]
            # Set the result
            future.set_result({
                "type": "response",
                "id": list(client.pending_commands.keys())[0],
                "command": "testCommand",
                "data": {"result": "success"},
                "timestamp": "2023-01-01T00:00:00Z",
            })
        
        with patch.object(client, '_receive_messages', side_effect=mock_receive):
            response = await client.send_command("testCommand", {"param": "value"})
            
            assert response["command"] == "testCommand"
            assert response["data"]["result"] == "success"

@pytest.mark.asyncio
async def test_event_handlers(mock_websocket):
    """Test event handlers."""
    with patch('websockets.connect', return_value=mock_websocket):
        client = WhatsAppGatewayClient("ws://localhost:8090/ws")
        
        # Create mock event handler
        mock_handler = MagicMock()
        
        async def async_handler(data):
            mock_handler(data)
        
        # Register event handler
        client.register_event_handler("test_event", async_handler)
        
        # Dispatch event
        test_data = {"test": "data"}
        await client._dispatch_event("test_event", test_data)
        
        # Check that handler was called
        mock_handler.assert_called_once_with(test_data)
        
        # Unregister event handler
        client.unregister_event_handler("test_event", async_handler)
        
        # Reset mock
        mock_handler.reset_mock()
        
        # Dispatch event again
        await client._dispatch_event("test_event", test_data)
        
        # Check that handler was not called
        mock_handler.assert_not_called()

@pytest.mark.asyncio
async def test_connection_callbacks(mock_websocket):
    """Test connection callbacks."""
    with patch('websockets.connect', return_value=mock_websocket):
        client = WhatsAppGatewayClient("ws://localhost:8090/ws")
        
        # Create mock callbacks
        mock_connect = MagicMock()
        mock_disconnect = MagicMock()
        
        async def async_connect():
            mock_connect()
        
        async def async_disconnect():
            mock_disconnect()
        
        # Register callbacks
        client.on_connect(async_connect)
        client.on_disconnect(async_disconnect)
        
        # Connect
        await client.connect()
        
        # Check that connect callback was called
        mock_connect.assert_called_once()
        
        # Disconnect
        await client.disconnect()
        
        # Check that disconnect callback was called
        mock_disconnect.assert_called_once()
