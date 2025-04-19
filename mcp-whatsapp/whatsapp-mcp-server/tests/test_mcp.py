"""
Tests for MCP handler.

@author Bruno Santos
"""

import os
import json
import asyncio
import pytest
from unittest.mock import MagicMock, patch
from fastapi import WebSocket

from src.mcp.handler import MCPHandler
from src.websocket.client import WhatsAppGatewayClient
from src.models.cache import CacheManager

# Setup test fixtures
@pytest.fixture
def mock_gateway_client():
    """Create a mock WhatsApp Gateway client."""
    client = MagicMock(spec=WhatsAppGatewayClient)
    client.is_connected.return_value = True
    client.is_authenticated.return_value = True
    
    async def mock_send_command(command, data=None):
        """Mock send_command method."""
        if command == "getContacts":
            return {
                "command": "getContacts",
                "data": {
                    "contacts": [
                        {
                            "id": "contact1",
                            "name": "Contact 1",
                            "number": "123456789",
                            "isGroup": False,
                            "isMyContact": True,
                        },
                        {
                            "id": "group1",
                            "name": "Group 1",
                            "number": "",
                            "isGroup": True,
                            "isMyContact": False,
                        },
                    ]
                }
            }
        elif command == "getChats":
            return {
                "command": "getChats",
                "data": {
                    "chats": [
                        {
                            "id": "chat1",
                            "name": "Chat 1",
                            "isGroup": False,
                            "timestamp": "2023-01-01T00:00:00Z",
                            "unreadCount": 0,
                        },
                        {
                            "id": "chat2",
                            "name": "Group 1",
                            "isGroup": True,
                            "timestamp": "2023-01-01T00:00:00Z",
                            "unreadCount": 2,
                        },
                    ]
                }
            }
        elif command == "getChatMessages":
            return {
                "command": "getChatMessages",
                "data": {
                    "messages": [
                        {
                            "id": "msg1",
                            "chatId": data.get("chatId"),
                            "content": "Hello",
                            "timestamp": "2023-01-01T00:00:00Z",
                            "sender": {
                                "id": "sender1",
                                "name": "Sender 1",
                            },
                            "hasMedia": False,
                            "isGroup": False,
                            "isForwarded": False,
                            "mentionedIds": [],
                        }
                    ]
                }
            }
        elif command == "sendMessage":
            return {
                "command": "sendMessage",
                "data": {
                    "message": {
                        "id": "newMsg1",
                        "chatId": data.get("chatId"),
                        "content": data.get("content"),
                        "timestamp": "2023-01-01T00:00:00Z",
                        "sender": {
                            "id": "me",
                            "name": "Me",
                        },
                        "hasMedia": False,
                        "isGroup": False,
                        "isForwarded": False,
                        "mentionedIds": [],
                    }
                }
            }
        else:
            return {
                "command": command,
                "data": {}
            }
    
    client.send_command = mock_send_command
    
    return client

@pytest.fixture
def mock_cache_manager():
    """Create a mock cache manager."""
    cache = MagicMock(spec=CacheManager)
    
    async def mock_get(key):
        """Mock get method."""
        return None
    
    async def mock_set(key, value, ttl=None):
        """Mock set method."""
        pass
    
    async def mock_stats():
        """Mock stats method."""
        return {
            "memory": {
                "size": 0,
                "max_size": 1000,
                "ttl": 86400,
            },
            "disk": {},
        }
    
    cache.get = mock_get
    cache.set = mock_set
    cache.get_contacts = mock_get
    cache.set_contacts = mock_set
    cache.get_chats = mock_get
    cache.set_chats = mock_set
    cache.get_chat_messages = mock_get
    cache.set_chat_messages = mock_set
    cache.stats = mock_stats
    
    return cache

@pytest.fixture
def mcp_handler(mock_gateway_client, mock_cache_manager):
    """Create a MCP handler for testing."""
    return MCPHandler(mock_gateway_client, mock_cache_manager)

@pytest.fixture
def mock_websocket():
    """Create a mock WebSocket."""
    ws = MagicMock(spec=WebSocket)
    
    async def mock_send_json(data):
        """Mock send_json method."""
        return data
    
    ws.send_json = mock_send_json
    
    return ws

# Test cases
@pytest.mark.asyncio
async def test_get_contacts(mcp_handler):
    """Test getting contacts."""
    response = await mcp_handler.handle_get_contacts("test_client", {"command": "getContacts"})
    
    assert response["success"] is True
    assert len(response["contacts"]) == 2
    assert response["contacts"][0]["name"] == "Contact 1"
    assert response["contacts"][1]["isGroup"] is True

@pytest.mark.asyncio
async def test_get_chats(mcp_handler):
    """Test getting chats."""
    response = await mcp_handler.handle_get_chats("test_client", {"command": "getChats"})
    
    assert response["success"] is True
    assert len(response["chats"]) == 2
    assert response["chats"][0]["name"] == "Chat 1"
    assert response["chats"][1]["isGroup"] is True
    assert response["chats"][1]["unreadCount"] == 2

@pytest.mark.asyncio
async def test_get_chat_messages(mcp_handler):
    """Test getting chat messages."""
    response = await mcp_handler.handle_get_chat_messages(
        "test_client",
        {
            "command": "getChatMessages",
            "data": {
                "chatId": "chat1",
            },
        },
    )
    
    assert response["success"] is True
    assert len(response["messages"]) == 1
    assert response["messages"][0]["content"] == "Hello"

@pytest.mark.asyncio
async def test_send_message(mcp_handler):
    """Test sending a message."""
    response = await mcp_handler.handle_send_message(
        "test_client",
        {
            "command": "sendMessage",
            "data": {
                "chatId": "chat1",
                "content": "Hello, world!",
            },
        },
    )
    
    assert response["success"] is True
    assert response["message"]["content"] == "Hello, world!"
    assert response["message"]["sender"]["name"] == "Me"

@pytest.mark.asyncio
async def test_register_unregister_client(mcp_handler, mock_websocket):
    """Test registering and unregistering a client."""
    client_id = "test_client"
    
    # Register client
    mcp_handler.register_claude_client(client_id, mock_websocket)
    assert client_id in mcp_handler.claude_clients
    
    # Unregister client
    mcp_handler.unregister_claude_client(client_id)
    assert client_id not in mcp_handler.claude_clients
