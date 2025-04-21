"""
Message models for the MCP WhatsApp Server.

@author Bruno Santos
"""

from datetime import datetime
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field

class MessageSender(BaseModel):
    """Model for message sender."""
    
    id: str = Field(...)
    name: str = Field(default="")

class Message(BaseModel):
    """Model for WhatsApp message."""
    
    id: str = Field(...)
    chat_id: str = Field(...)
    content: str = Field(default="")
    timestamp: datetime = Field(default_factory=datetime.now)
    sender: MessageSender = Field(...)
    has_media: bool = Field(default=False)
    is_group: bool = Field(default=False)
    is_forwarded: bool = Field(default=False)
    mentioned_ids: List[str] = Field(default_factory=list)
    media_url: Optional[str] = Field(default=None)
    media_type: Optional[str] = Field(default=None)
    
    class Config:
        """Pydantic configuration."""
        
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }
    
    @classmethod
    def from_gateway(cls, data: Dict[str, Any]) -> "Message":
        """Create a Message from WhatsApp Gateway data."""
        return cls(
            id=data.get("id", ""),
            chat_id=data.get("chatId", ""),
            content=data.get("content", ""),
            timestamp=datetime.fromisoformat(data.get("timestamp", datetime.now().isoformat())),
            sender=MessageSender(
                id=data.get("sender", {}).get("id", ""),
                name=data.get("sender", {}).get("name", ""),
            ),
            has_media=data.get("hasMedia", False),
            is_group=data.get("isGroup", False),
            is_forwarded=data.get("isForwarded", False),
            mentioned_ids=data.get("mentionedIds", []),
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the message to a dictionary."""
        return {
            "id": self.id,
            "chatId": self.chat_id,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "sender": {
                "id": self.sender.id,
                "name": self.sender.name,
            },
            "hasMedia": self.has_media,
            "isGroup": self.is_group,
            "isForwarded": self.is_forwarded,
            "mentionedIds": self.mentioned_ids,
            "mediaUrl": self.media_url,
            "mediaType": self.media_type,
        }

class MessageRequest(BaseModel):
    """Model for message request from Claude Desktop."""
    
    chat_id: str = Field(...)
    content: str = Field(...)

class MediaMessageRequest(BaseModel):
    """Model for media message request from Claude Desktop."""
    
    chat_id: str = Field(...)
    media: str = Field(...)  # Base64 encoded media
    filename: str = Field(...)
    caption: Optional[str] = Field(default=None)
    media_type: Optional[str] = Field(default=None)

class MessageResponse(BaseModel):
    """Model for message response to Claude Desktop."""
    
    success: bool = Field(default=True)
    message: Optional[Message] = Field(default=None)
    error: Optional[str] = Field(default=None)

class MessagesResponse(BaseModel):
    """Model for multiple messages response to Claude Desktop."""
    
    success: bool = Field(default=True)
    messages: List[Message] = Field(default_factory=list)
    error: Optional[str] = Field(default=None)
