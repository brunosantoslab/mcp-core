"""
Cache manager for the MCP WhatsApp Server.

@author Bruno Santos
"""

import os
import json
import time
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from diskcache import Cache
from expiringdict import ExpiringDict

from ..utils.logger import logger

class CacheManager:
    """Cache manager for the MCP WhatsApp Server."""
    
    def __init__(self, cache_dir: str, ttl: int = 86400):
        """Initialize the cache manager."""
        self.cache_dir = Path(cache_dir)
        self.ttl = ttl
        
        # Create cache directory if it doesn't exist
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize disk cache
        self.disk_cache = Cache(directory=str(self.cache_dir / "disk_cache"))
        
        # Initialize memory cache
        self.memory_cache: ExpiringDict = ExpiringDict(
            max_len=1000,  # Maximum number of items in the cache
            max_age_seconds=ttl,  # TTL in seconds
        )
        
        # Lock for cache operations
        self.lock = asyncio.Lock()
    
    async def get(self, key: str) -> Optional[Any]:
        """Get a value from the cache."""
        # Try memory cache first
        value = self.memory_cache.get(key)
        if value is not None:
            logger.debug(f"Cache hit (memory): {key}")
            return value
        
        # Try disk cache
        async with self.lock:
            if key in self.disk_cache:
                value = self.disk_cache[key]
                # Update memory cache
                self.memory_cache[key] = value
                logger.debug(f"Cache hit (disk): {key}")
                return value
        
        logger.debug(f"Cache miss: {key}")
        return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set a value in the cache."""
        # Set in memory cache
        self.memory_cache[key] = value
        
        # Set in disk cache
        async with self.lock:
            self.disk_cache.set(key, value, expire=ttl or self.ttl)
        
        logger.debug(f"Cache set: {key}")
    
    async def delete(self, key: str) -> None:
        """Delete a value from the cache."""
        # Delete from memory cache
        if key in self.memory_cache:
            del self.memory_cache[key]
        
        # Delete from disk cache
        async with self.lock:
            if key in self.disk_cache:
                del self.disk_cache[key]
        
        logger.debug(f"Cache delete: {key}")
    
    async def clear(self) -> None:
        """Clear the cache."""
        # Clear memory cache
        self.memory_cache.clear()
        
        # Clear disk cache
        async with self.lock:
            self.disk_cache.clear()
        
        logger.info("Cache cleared")
    
    async def close(self) -> None:
        """Close the cache."""
        # Close disk cache
        async with self.lock:
            self.disk_cache.close()
        
        logger.info("Cache closed")
    
    async def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        disk_stats = {}
        
        async with self.lock:
            disk_stats = dict(self.disk_cache.stats())
        
        return {
            "memory": {
                "size": len(self.memory_cache),
                "max_size": self.memory_cache.max_len,
                "ttl": self.memory_cache.max_age_seconds,
            },
            "disk": disk_stats,
        }
    
    # Specialized cache methods for WhatsApp data
    
    async def get_contacts(self) -> Optional[List[Dict[str, Any]]]:
        """Get contacts from the cache."""
        return await self.get("contacts")
    
    async def set_contacts(self, contacts: List[Dict[str, Any]]) -> None:
        """Set contacts in the cache."""
        await self.set("contacts", contacts)
    
    async def get_chats(self) -> Optional[List[Dict[str, Any]]]:
        """Get chats from the cache."""
        return await self.get("chats")
    
    async def set_chats(self, chats: List[Dict[str, Any]]) -> None:
        """Set chats in the cache."""
        await self.set("chats", chats)
    
    async def get_chat_messages(self, chat_id: str) -> Optional[List[Dict[str, Any]]]:
        """Get chat messages from the cache."""
        return await self.get(f"chat_messages:{chat_id}")
    
    async def set_chat_messages(self, chat_id: str, messages: List[Dict[str, Any]]) -> None:
        """Set chat messages in the cache."""
        await self.set(f"chat_messages:{chat_id}", messages)
    
    async def add_chat_message(self, chat_id: str, message: Dict[str, Any]) -> None:
        """Add a message to the chat messages cache."""
        messages = await self.get_chat_messages(chat_id) or []
        
        # Check if message already exists
        for i, msg in enumerate(messages):
            if msg.get("id") == message.get("id"):
                # Update existing message
                messages[i] = message
                await self.set_chat_messages(chat_id, messages)
                return
        
        # Add new message
        messages.append(message)
        
        # Sort messages by timestamp
        messages.sort(key=lambda m: m.get("timestamp", ""), reverse=True)
        
        await self.set_chat_messages(chat_id, messages)
    
    async def get_qr_code(self) -> Optional[str]:
        """Get the QR code from the cache."""
        return await self.get("qr_code")
    
    async def set_qr_code(self, qr_code: str) -> None:
        """Set the QR code in the cache."""
        await self.set("qr_code", qr_code, ttl=300)  # 5 minutes TTL
