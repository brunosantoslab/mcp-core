"""
Claude Desktop integration module.

@author Bruno Santos
"""

import json
import asyncio
from typing import Dict, Any, List, Optional

from ..utils.logger import logger
from ..models.message import Message
from ..models.contact import Contact, Chat

class ClaudeIntegration:
    """Claude Desktop integration helper class."""
    
    @staticmethod
    def format_contacts_for_claude(contacts: List[Dict[str, Any]]) -> str:
        """Format contacts for Claude in a readable format."""
        if not contacts:
            return "No contacts found."
        
        result = "Contacts:\n\n"
        
        # Group by regular contacts and groups
        regular_contacts = []
        groups = []
        
        for contact in contacts:
            if contact.get("isGroup"):
                groups.append(contact)
            else:
                regular_contacts.append(contact)
        
        # Format regular contacts
        if regular_contacts:
            result += "Individual Contacts:\n"
            for contact in regular_contacts:
                name = contact.get("name") or "Unknown"
                number = contact.get("number") or "Unknown"
                result += f"- {name} ({number})\n"
        
        # Format groups
        if groups:
            result += "\nGroups:\n"
            for group in groups:
                name = group.get("name") or "Unknown Group"
                result += f"- {name}\n"
        
        return result
    
    @staticmethod
    def format_chats_for_claude(chats: List[Dict[str, Any]]) -> str:
        """Format chats for Claude in a readable format."""
        if not chats:
            return "No chats found."
        
        result = "Chats:\n\n"
        
        # Group by regular chats and groups
        regular_chats = []
        group_chats = []
        
        for chat in chats:
            if chat.get("isGroup"):
                group_chats.append(chat)
            else:
                regular_chats.append(chat)
        
        # Format regular chats
        if regular_chats:
            result += "Individual Chats:\n"
            for chat in regular_chats:
                name = chat.get("name") or "Unknown"
                unread = chat.get("unreadCount", 0)
                unread_text = f" ({unread} unread)" if unread > 0 else ""
                result += f"- {name}{unread_text}\n"
        
        # Format group chats
        if group_chats:
            result += "\nGroup Chats:\n"
            for chat in group_chats:
                name = chat.get("name") or "Unknown Group"
                unread = chat.get("unreadCount", 0)
                unread_text = f" ({unread} unread)" if unread > 0 else ""
                result += f"- {name}{unread_text}\n"
        
        return result
    
    @staticmethod
    def format_messages_for_claude(messages: List[Dict[str, Any]], chat_name: Optional[str] = None) -> str:
        """Format messages for Claude in a readable format."""
        if not messages:
            return "No messages found."
        
        header = f"Messages{' from ' + chat_name if chat_name else ''}:\n\n"
        result = header
        
        # Show messages in reverse chronological order (newest first)
        for message in messages:
            sender_name = message.get("sender", {}).get("name") or "Unknown"
            content = message.get("content") or "[Media]" if message.get("hasMedia") else "[Empty]"
            timestamp = message.get("timestamp", "").split("T")[0]  # Just the date part
            
            result += f"{sender_name} ({timestamp}):\n{content}\n\n"
        
        return result
    
    @staticmethod
    def parse_claude_message(message: str) -> Dict[str, Any]:
        """Parse a message from Claude to extract commands."""
        command = None
        data = {}
        
        # Check for send message command
        # Format: "send message to <contact/group name>: <message content>"
        if "send message to " in message.lower():
            parts = message.split(":", 1)
            if len(parts) == 2:
                command = "sendMessage"
                recipient = parts[0].lower().replace("send message to ", "").strip()
                content = parts[1].strip()
                data = {
                    "recipient": recipient,
                    "content": content,
                }
        
        # Check for get contacts command
        # Format: "show contacts" or "list contacts"
        elif any(cmd in message.lower() for cmd in ["show contacts", "list contacts", "get contacts"]):
            command = "getContacts"
        
        # Check for get chats command
        # Format: "show chats" or "list chats"
        elif any(cmd in message.lower() for cmd in ["show chats", "list chats", "get chats"]):
            command = "getChats"
        
        # Check for get messages command
        # Format: "show messages from <contact/group name>" or "get messages from <contact/group name>"
        elif any(cmd in message.lower() for cmd in ["show messages from ", "get messages from "]):
            command = "getChatMessages"
            for prefix in ["show messages from ", "get messages from "]:
                if prefix in message.lower():
                    chat_name = message.lower().replace(prefix, "").strip()
                    data = {
                        "chatName": chat_name,
                    }
                    break
        
        # Check for search messages command
        # Format: "search messages for <query>" or "find messages containing <query>"
        elif any(cmd in message.lower() for cmd in ["search messages for ", "find messages containing "]):
            command = "searchMessages"
            query = ""
            chat_name = None
            
            if "search messages for " in message.lower():
                query_part = message.lower().replace("search messages for ", "").strip()
            elif "find messages containing " in message.lower():
                query_part = message.lower().replace("find messages containing ", "").strip()
            
            # Check if the search is scoped to a specific chat
            if " in chat " in query_part:
                query_parts = query_part.split(" in chat ")
                if len(query_parts) == 2:
                    query = query_parts[0].strip()
                    chat_name = query_parts[1].strip()
            else:
                query = query_part
            
            data = {
                "query": query,
                "chatName": chat_name,
            }
        
        return {
            "command": command,
            "data": data,
        }
