"""
MCP WhatsApp Server main module.
Handles the communication between Claude Desktop and the WhatsApp Gateway
using FastMCP to simplify the MCP protocol.

@author Bruno Santos
"""
import sys
import signal
import asyncio
from mcp.server.fastmcp import FastMCP
from typing import Dict, Any, List, Optional

from .utils.logger import logger
from .utils.config import load_config
from .websocket.client import WhatsAppGatewayClient
from .models.cache import CacheManager

# Load configuration
config = load_config()

# Initialize cache manager
cache_manager = CacheManager(config.cache_dir)

# Initialize WhatsApp Gateway client
gateway_client = WhatsAppGatewayClient(
    ws_url=f"ws://{config.gateway_host}:{config.gateway_port}{config.gateway_path}",
    reconnect_interval=config.reconnect_interval,
    max_reconnect_attempts=config.max_reconnect_attempts,
)

# Initialize FastMCP server
mcp = FastMCP("whatsapp")


# Helper function to ensure connection
async def ensure_connection() -> bool:
    """Ensure connection to WhatsApp Gateway, reconnect if needed."""
    if not gateway_client.is_connected():
        logger.warning("Not connected to WhatsApp Gateway. Attempting to connect...")
        try:
            connection_success = await gateway_client.connect()
            if gateway_client.is_connected():
                logger.info("Successfully connected to WhatsApp Gateway")
                return True
            else:
                logger.error("Failed to connect to WhatsApp Gateway despite successful connection call")
                return False
        except Exception as e:
            logger.error(f"Error connecting to WhatsApp Gateway: {e}")
            return False
    return True


@mcp.tool()
async def startup():
    """Initialize services on startup."""
    logger.info("Initializing WhatsApp MCP Server...")
    
    # Connect to WhatsApp Gateway with retry mechanism
    connect_success = False
    max_attempts = 5
    
    for attempt in range(1, max_attempts + 1):
        try:
            logger.info(f"Connecting to WhatsApp Gateway (attempt {attempt}/{max_attempts})...")
            await gateway_client.connect()
            
            if gateway_client.is_connected():
                connect_success = True
                logger.info("Connected to WhatsApp Gateway successfully")
                break
            else:
                logger.warning("Connection attempt completed but gateway not connected")
                await asyncio.sleep(2)  # Short wait between attempts
                
        except Exception as e:
            logger.warning(f"Could not connect to WhatsApp Gateway on attempt {attempt}: {e}")
            await asyncio.sleep(2)  # Short wait between attempts
    
    if not connect_success:
        logger.warning("Could not establish connection to WhatsApp Gateway during startup")
        logger.info("Server will continue to run and retry connection in background")
    
    logger.info(f"WhatsApp MCP Server started")


@mcp.tool()
async def shutdown():
    """Clean up resources on shutdown."""
    logger.info("Shutting down WhatsApp MCP Server...")
    await gateway_client.disconnect()
    await cache_manager.close()
    logger.info("WhatsApp MCP Server shutdown complete")


# Tools for WhatsApp integration

@mcp.tool()
async def get_contacts(query: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get WhatsApp contacts, optionally filtered by query.
    
    Args:
        query: Optional search term to filter contacts by name or number
    """
    try:
        # Check cache first
        cached_contacts = await cache_manager.get_contacts()
        
        if cached_contacts:
            logger.debug("Returning contacts from cache")
            
            # Filter contacts if query is provided
            if query and cached_contacts:
                query = query.lower()
                filtered_contacts = [
                    contact for contact in cached_contacts
                    if query in contact.get("name", "").lower() or query in contact.get("number", "").lower()
                ]
                return filtered_contacts
            
            return cached_contacts
        
        # Ensure connection to Gateway
        if not await ensure_connection():
            logger.error("Failed to connect to WhatsApp Gateway. Cannot get contacts.")
            return []
        
        # Get contacts from WhatsApp Gateway
        response = await gateway_client.send_command("getContacts")
        
        if "data" in response and "contacts" in response["data"]:
            contacts = response["data"]["contacts"]
            
            # Cache contacts
            await cache_manager.set_contacts(contacts)
            
            # Filter contacts if query is provided
            if query:
                query = query.lower()
                filtered_contacts = [
                    contact for contact in contacts
                    if query in contact.get("name", "").lower() or query in contact.get("number", "").lower()
                ]
                return filtered_contacts
            
            return contacts
        
        return []
    except Exception as e:
        logger.exception(f"Error getting contacts: {e}")
        return []


@mcp.tool()
async def get_chats(query: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get WhatsApp chats, optionally filtered by query.
    
    Args:
        query: Optional search term to filter chats by name
    """
    try:
        # Check cache first
        cached_chats = await cache_manager.get_chats()
        
        if cached_chats:
            logger.debug("Returning chats from cache")
            
            # Filter chats if query is provided
            if query and cached_chats:
                query = query.lower()
                filtered_chats = [
                    chat for chat in cached_chats
                    if query in chat.get("name", "").lower()
                ]
                return filtered_chats
            
            return cached_chats
        
        # Ensure connection to Gateway
        if not await ensure_connection():
            logger.error("Failed to connect to WhatsApp Gateway. Cannot get chats.")
            return []
        
        # Get chats from WhatsApp Gateway
        response = await gateway_client.send_command("getChats")
        
        if "data" in response and "chats" in response["data"]:
            chats = response["data"]["chats"]
            
            # Cache chats
            await cache_manager.set_chats(chats)
            
            # Filter chats if query is provided
            if query:
                query = query.lower()
                filtered_chats = [
                    chat for chat in chats
                    if query in chat.get("name", "").lower()
                ]
                return filtered_chats
            
            return chats
        
        return []
    except Exception as e:
        logger.exception(f"Error getting chats: {e}")
        return []


@mcp.tool()
async def get_chat_messages(
    chat_id: str,
    limit: int = 50,
    query: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Get messages from a WhatsApp chat.
    
    Args:
        chat_id: ID of the chat to get messages from
        limit: Maximum number of messages to return
        query: Optional search term to filter messages by content
    """
    try:
        if not chat_id:
            logger.error("No chat_id provided")
            return []
        
        # Check cache first
        cached_messages = await cache_manager.get_chat_messages(chat_id)
        
        if cached_messages:
            logger.debug(f"Returning messages for chat {chat_id} from cache")
            
            # Filter messages if query is provided
            if query:
                query = query.lower()
                filtered_messages = [
                    msg for msg in cached_messages
                    if query in msg.get("content", "").lower()
                ]
                return filtered_messages[:limit]
            
            return cached_messages[:limit]
        
        # Ensure connection to Gateway
        if not await ensure_connection():
            logger.error("Failed to connect to WhatsApp Gateway. Cannot get chat messages.")
            return []
        
        # Get messages from WhatsApp Gateway
        response = await gateway_client.send_command(
            "getChatMessages",
            {"chatId": chat_id, "limit": limit}
        )
        
        if "data" in response and "messages" in response["data"]:
            messages = response["data"]["messages"]
            
            # Cache messages
            await cache_manager.set_chat_messages(chat_id, messages)
            
            # Filter messages if query is provided
            if query:
                query = query.lower()
                filtered_messages = [
                    msg for msg in messages
                    if query in msg.get("content", "").lower()
                ]
                return filtered_messages
            
            return messages
        
        return []
    except Exception as e:
        logger.exception(f"Error getting chat messages: {e}")
        return []


@mcp.tool()
async def send_message(
    chat_id: str,
    content: str
) -> Dict[str, Any]:
    """Send a message to a WhatsApp chat.
    
    Args:
        chat_id: ID of the chat to send message to
        content: Content of the message to send
    """
    try:
        if not chat_id or not content:
            logger.error("Missing chat_id or content")
            return {"success": False, "error": "Missing chat_id or content"}
        
        # Ensure connection to Gateway
        if not await ensure_connection():
            logger.error("Failed to connect to WhatsApp Gateway. Cannot send message.")
            return {"success": False, "error": "Failed to connect to WhatsApp Gateway"}
        
        # Send message to WhatsApp Gateway
        response = await gateway_client.send_command(
            "sendMessage",
            {"chatId": chat_id, "content": content}
        )
        
        if "data" in response and "message" in response["data"]:
            sent_message = response["data"]["message"]
            
            # Add to cache
            chat_id = sent_message.get("chatId")
            if chat_id:
                await cache_manager.add_chat_message(chat_id, sent_message)
            
            return {"success": True, "message": sent_message}
        
        return {"success": False, "error": "Failed to send message"}
    except Exception as e:
        logger.exception(f"Error sending message: {e}")
        return {"success": False, "error": str(e)}


@mcp.tool()
async def send_media(
    chat_id: str,
    media: str,  # Base64 encoded media
    filename: str,
    caption: Optional[str] = None,
    media_type: Optional[str] = None
) -> Dict[str, Any]:
    """Send media to a WhatsApp chat.
    
    Args:
        chat_id: ID of the chat to send media to
        media: Base64 encoded media content
        filename: Name of the media file
        caption: Optional caption for the media
        media_type: Optional type of media (image, video, audio, document)
    """
    try:
        if not chat_id or not media or not filename:
            logger.error("Missing required parameters")
            return {"success": False, "error": "Missing required parameters"}
        
        # Ensure connection to Gateway
        if not await ensure_connection():
            logger.error("[MEDIA] Failed to connect to WhatsApp Gateway. Cannot send media.")
            return {"success": False, "error": "Failed to connect to WhatsApp Gateway"}
        
        # Calculate media size
        media_size_kb = len(media) / 1024
        logger.info(f"[MEDIA] Sending media to chat {chat_id}: filename={filename}, size={media_size_kb:.2f}KB, type={media_type}")
        
        # Size verification
        MAX_SIZE_KB = 5000  # 5MB in Base64
        if media_size_kb > MAX_SIZE_KB:
            logger.warning(f"[MEDIA] Large media being sent: {media_size_kb:.2f}KB. May cause timeout issues.")
        
        # Validate media type
        valid_types = ["image", "video", "audio", "document"]
        if media_type and media_type not in valid_types:
            logger.warning(f"[MEDIA] Potentially invalid media type: {media_type}")
        
        # Calculate appropriate timeout based on media size (min 2 minutes, max 10 minutes)
        dynamic_timeout = min(600, max(120, int(media_size_kb / 10)))
        logger.info(f"[MEDIA] Using timeout of {dynamic_timeout} seconds for media send")
        
        logger.info(f"[MEDIA] Calling gateway sendMedia command")
        
        # Send media to WhatsApp Gateway with dynamic timeout
        try:
            response = await gateway_client.send_command(
                "sendMedia",
                {
                    "chatId": chat_id,
                    "media": media,
                    "filename": filename,
                    "caption": caption,
                    "mediaType": media_type
                },
                timeout=dynamic_timeout
            )
            
            logger.info(f"[MEDIA] Gateway response received: success={response.get('success', False)}")
            
            if "error" in response:
                logger.error(f"[MEDIA] Gateway error: {response['error']}")
                return {"success": False, "error": response["error"]}
            
            if "data" in response and "message" in response["data"]:
                sent_message = response["data"]["message"]
                
                # Add to cache
                chat_id = sent_message.get("chatId")
                if chat_id:
                    await cache_manager.add_chat_message(chat_id, sent_message)
                
                logger.info(f"[MEDIA] Media successfully sent and cached")
                return {"success": True, "message": sent_message}
            
            logger.error(f"[MEDIA] Unexpected response format: {response}")
            return {"success": False, "error": "Failed to send media: Unexpected response format"}
        
        except asyncio.TimeoutError:
            logger.error(f"[MEDIA] Operation timed out after {dynamic_timeout} seconds")
            return {"success": False, "error": f"Media send operation timed out after {dynamic_timeout} seconds"}
        
        except Exception as cmd_error:
            logger.error(f"[MEDIA] Error during gateway command: {cmd_error}")
            return {"success": False, "error": f"Error communicating with Gateway: {str(cmd_error)}"}
        
    except Exception as e:
        logger.exception(f"[MEDIA] Unhandled exception in send_media: {e}")
        return {"success": False, "error": str(e)}


@mcp.tool()
async def search_messages(
    query: str,
    chat_id: Optional[str] = None,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """Search for messages in WhatsApp chats.
    
    Args:
        query: Search term to filter messages by content
        chat_id: Optional chat ID to limit search to a specific chat
        limit: Maximum number of messages to return
    """
    try:
        if not query:
            logger.error("No query provided")
            return []
        
        # Ensure connection to Gateway
        if not await ensure_connection():
            logger.error("Failed to connect to WhatsApp Gateway. Cannot search messages.")
            return []
        
        query = query.lower()
        results = []
        
        # Search in specific chat if chat_id is provided
        if chat_id:
            messages = await get_chat_messages(chat_id, limit, query)
            return messages
        
        # Search in all chats
        chats = await get_chats()
        
        for chat in chats[:10]:  # Limit to 10 chats for performance
            chat_id = chat.get("id")
            if chat_id:
                messages = await get_chat_messages(chat_id, limit // 10, query)  # Distribute limit among chats
                results.extend(messages)
        
        # Sort results by timestamp (newest first)
        results.sort(key=lambda m: m.get("timestamp", ""), reverse=True)
        
        return results[:limit]
    except Exception as e:
        logger.exception(f"Error searching messages: {e}")
        return []


def main():
    """Entry point for the application."""
    # Setup signal handlers
    def signal_handler(sig, frame):
        logger.info(f"Received signal {sig}, shutting down...")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Run the MCP server
    logger.info("Starting WhatsApp MCP Server...")


if __name__ == "__main__":
    mcp.run(transport='stdio')