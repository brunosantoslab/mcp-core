"""
Tests for cache manager.

@author Bruno Santos
"""
import asyncio
import pytest
import tempfile
import shutil

from src.models.cache import CacheManager

# Setup test fixtures
@pytest.fixture
def temp_cache_dir():
    """Create a temporary directory for cache."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture
def cache_manager(temp_cache_dir):
    """Create a cache manager for testing."""
    cache = CacheManager(temp_cache_dir, ttl=10)  # Short TTL for testing
    yield cache
    asyncio.run(cache.close())

# Test cases
@pytest.mark.asyncio
async def test_set_get(cache_manager):
    """Test setting and getting a value from the cache."""
    key = "test_key"
    value = {"test": "value"}
    
    # Set value
    await cache_manager.set(key, value)
    
    # Get value
    result = await cache_manager.get(key)
    
    assert result == value

@pytest.mark.asyncio
async def test_delete(cache_manager):
    """Test deleting a value from the cache."""
    key = "test_key"
    value = {"test": "value"}
    
    # Set value
    await cache_manager.set(key, value)
    
    # Delete value
    await cache_manager.delete(key)
    
    # Get value
    result = await cache_manager.get(key)
    
    assert result is None

@pytest.mark.asyncio
async def test_clear(cache_manager):
    """Test clearing the cache."""
    # Set multiple values
    await cache_manager.set("key1", "value1")
    await cache_manager.set("key2", "value2")
    
    # Clear cache
    await cache_manager.clear()
    
    # Get values
    result1 = await cache_manager.get("key1")
    result2 = await cache_manager.get("key2")
    
    assert result1 is None
    assert result2 is None

@pytest.mark.asyncio
async def test_stats(cache_manager):
    """Test getting cache statistics."""
    # Set value
    await cache_manager.set("key1", "value1")
    
    # Get stats
    stats = await cache_manager.stats()
    
    assert "memory" in stats
    assert "disk" in stats
    assert stats["memory"]["size"] == 1
    assert stats["memory"]["max_size"] == 1000

@pytest.mark.asyncio
async def test_ttl(cache_manager):
    """Test time-to-live functionality."""
    key = "test_key"
    value = {"test": "value"}
    
    # Set value with very short TTL
    await cache_manager.set(key, value, ttl=1)
    
    # Get value immediately
    result1 = await cache_manager.get(key)
    
    # Wait for TTL to expire
    await asyncio.sleep(2)
    
    # Get value after TTL expired
    result2 = await cache_manager.get(key)
    
    assert result1 == value
    assert result2 is None

@pytest.mark.asyncio
async def test_contacts_cache(cache_manager):
    """Test contacts cache methods."""
    contacts = [
        {"id": "contact1", "name": "Contact 1"},
        {"id": "contact2", "name": "Contact 2"},
    ]
    
    # Set contacts
    await cache_manager.set_contacts(contacts)
    
    # Get contacts
    result = await cache_manager.get_contacts()
    
    assert result == contacts

@pytest.mark.asyncio
async def test_chats_cache(cache_manager):
    """Test chats cache methods."""
    chats = [
        {"id": "chat1", "name": "Chat 1"},
        {"id": "chat2", "name": "Chat 2"},
    ]
    
    # Set chats
    await cache_manager.set_chats(chats)
    
    # Get chats
    result = await cache_manager.get_chats()
    
    assert result == chats

@pytest.mark.asyncio
async def test_chat_messages_cache(cache_manager):
    """Test chat messages cache methods."""
    chat_id = "chat1"
    messages = [
        {"id": "msg1", "content": "Hello"},
        {"id": "msg2", "content": "World"},
    ]
    
    # Set chat messages
    await cache_manager.set_chat_messages(chat_id, messages)
    
    # Get chat messages
    result = await cache_manager.get_chat_messages(chat_id)
    
    assert result == messages

@pytest.mark.asyncio
async def test_add_chat_message(cache_manager):
    """Test adding a message to chat messages cache."""
    chat_id = "chat1"
    messages = [
        {"id": "msg1", "content": "Hello", "timestamp": "2023-01-01T00:00:00Z"},
    ]
    
    # Set initial messages
    await cache_manager.set_chat_messages(chat_id, messages)
    
    # Add a new message
    new_message = {"id": "msg2", "content": "World", "timestamp": "2023-01-01T00:01:00Z"}
    await cache_manager.add_chat_message(chat_id, new_message)
    
    # Get updated messages
    result = await cache_manager.get_chat_messages(chat_id)
    
    assert len(result) == 2
    assert new_message in result
    
    # Update an existing message
    updated_message = {"id": "msg1", "content": "Updated", "timestamp": "2023-01-01T00:00:00Z"}
    await cache_manager.add_chat_message(chat_id, updated_message)
    
    # Get updated messages
    result = await cache_manager.get_chat_messages(chat_id)
    
    assert len(result) == 2
    assert updated_message in result
    assert new_message in result