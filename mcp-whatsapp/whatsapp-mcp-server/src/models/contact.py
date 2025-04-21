"""
Contact and chat models for the MCP WhatsApp Server.

@author Bruno Santos
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class Contact(BaseModel):
    """Model for WhatsApp contact."""
    
    id: str = Field(...)
    name: str = Field(default="")
    number: str = Field(default="")
    is_group: bool = Field(default=False)
    is_my_contact: bool = Field(default=False)
    
    @classmethod
    def from_gateway(cls, data: Dict[str, Any]) -> "Contact":
        """Create a Contact from WhatsApp Gateway data."""
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            number=data.get("number", ""),
            is_group=data.get("isGroup", False),
            is_my_contact=data.get("isMyContact", False),
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the contact to a dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "number": self.number,
            "isGroup": self.is_group,
            "isMyContact": self.is_my_contact,
        }

class Chat(BaseModel):
    """Model for WhatsApp chat."""
    
    id: str = Field(...)
    name: str = Field(default="")
    is_group: bool = Field(default=False)
    timestamp: str = Field(default="")
    unread_count: int = Field(default=0)
    
    @classmethod
    def from_gateway(cls, data: Dict[str, Any]) -> "Chat":
        """Create a Chat from WhatsApp Gateway data."""
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            is_group=data.get("isGroup", False),
            timestamp=data.get("timestamp", ""),
            unread_count=data.get("unreadCount", 0),
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the chat to a dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "isGroup": self.is_group,
            "timestamp": self.timestamp,
            "unreadCount": self.unread_count,
        }

class ContactsResponse(BaseModel):
    """Model for contacts response to Claude Desktop."""
    
    success: bool = Field(default=True)
    contacts: List[Contact] = Field(default_factory=list)
    error: Optional[str] = Field(default=None)

class ChatsResponse(BaseModel):
    """Model for chats response to Claude Desktop."""
    
    success: bool = Field(default=True)
    chats: List[Chat] = Field(default_factory=list)
    error: Optional[str] = Field(default=None)
