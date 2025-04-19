"""
Router for MCP API endpoints.

@author Bruno Santos
"""

import os
import json
import base64
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Request, Response, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from ..utils.logger import logger

# API Models
class MessageRequest(BaseModel):
    """Message request model."""
    
    chat_id: str = Field(...)
    content: str = Field(...)

class MediaMessageRequest(BaseModel):
    """Media message request model."""
    
    chat_id: str = Field(...)
    media: str = Field(...)  # Base64 encoded media
    filename: str = Field(...)
    caption: Optional[str] = Field(default=None)
    media_type: Optional[str] = Field(default=None)

class SearchRequest(BaseModel):
    """Search request model."""
    
    query: str = Field(...)
    chat_id: Optional[str] = Field(default=None)

# Create router
router = APIRouter()

# Helper function to get MCP handler
async def get_mcp_handler(request: Request):
    """Get the MCP handler from the request state."""
    return request.app.state.mcp_handler

@router.get("/contacts")
async def get_contacts(request: Request):
    """Get contacts endpoint."""
    mcp_handler = await get_mcp_handler(request)
    return await mcp_handler.handle_get_contacts("api", {"command": "getContacts"})

@router.get("/chats")
async def get_chats(request: Request):
    """Get chats endpoint."""
    mcp_handler = await get_mcp_handler(request)
    return await mcp_handler.handle_get_chats("api", {"command": "getChats"})

@router.get("/chats/{chat_id}/messages")
async def get_chat_messages(request: Request, chat_id: str, limit: int = 50):
    """Get chat messages endpoint."""
    mcp_handler = await get_mcp_handler(request)
    
    return await mcp_handler.handle_get_chat_messages(
        "api",
        {
            "command": "getChatMessages",
            "data": {
                "chatId": chat_id,
                "limit": limit,
            },
        },
    )

@router.post("/messages")
async def send_message(message_request: MessageRequest, request: Request):
    """Send message endpoint."""
    mcp_handler = await get_mcp_handler(request)
    
    return await mcp_handler.handle_send_message(
        "api",
        {
            "command": "sendMessage",
            "data": {
                "chatId": message_request.chat_id,
                "content": message_request.content,
            },
        },
    )

@router.post("/media")
async def send_media(media_request: MediaMessageRequest, request: Request):
    """Send media endpoint."""
    mcp_handler = await get_mcp_handler(request)
    
    return await mcp_handler.handle_send_media(
        "api",
        {
            "command": "sendMedia",
            "data": {
                "chatId": media_request.chat_id,
                "media": media_request.media,
                "filename": media_request.filename,
                "caption": media_request.caption,
                "mediaType": media_request.media_type,
            },
        },
    )

@router.post("/media/upload")
async def upload_media(
    request: Request,
    chat_id: str = Form(...),
    caption: Optional[str] = Form(None),
    file: UploadFile = File(...),
):
    """Upload media endpoint."""
    mcp_handler = await get_mcp_handler(request)
    
    try:
        # Read file contents
        contents = await file.read()
        
        # Convert to base64
        media_base64 = base64.b64encode(contents).decode("utf-8")
        
        # Determine media type from file extension
        filename = file.filename
        
        # Send media
        return await mcp_handler.handle_send_media(
            "api",
            {
                "command": "sendMedia",
                "data": {
                    "chatId": chat_id,
                    "media": media_base64,
                    "filename": filename,
                    "caption": caption,
                },
            },
        )
    except Exception as e:
        logger.exception(f"Error uploading media: {e}")
        raise HTTPException(status_code=500, detail=f"Error uploading media: {str(e)}")

@router.get("/auth/qrcode")
async def get_qr_code(request: Request):
    """Get QR code endpoint."""
    mcp_handler = await get_mcp_handler(request)
    return await mcp_handler.handle_get_qr_code("api", {"command": "getQRCode"})

@router.post("/search")
async def search_messages(search_request: SearchRequest, request: Request):
    """Search messages endpoint."""
    mcp_handler = await get_mcp_handler(request)
    
    return await mcp_handler.handle_search_messages(
        "api",
        {
            "command": "searchMessages",
            "data": {
                "query": search_request.query,
                "chatId": search_request.chat_id,
            },
        },
    )