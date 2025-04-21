"""
WebSocket client for communicating with the WhatsApp Gateway.

@author Bruno Santos
"""

import json
import asyncio
import uuid
from typing import Dict, Any, Optional, Callable, List, Set, Coroutine
import websockets
from websockets.exceptions import ConnectionClosed, WebSocketException

from ..utils.logger import logger

class WhatsAppGatewayClient:
    """WebSocket client for communicating with the WhatsApp Gateway."""
    
    def __init__(
        self,
        ws_url: str,
        reconnect_interval: int = 5,
        max_reconnect_attempts: int = 10,
    ):
        """Initialize the WhatsApp Gateway client."""
        self.ws_url = ws_url
        self.reconnect_interval = reconnect_interval
        self.max_reconnect_attempts = max_reconnect_attempts
        
        self.websocket = None
        self.connected = False
        self.authenticated = False
        self.reconnect_task = None
        self.receive_task = None
        
        # Command tracking
        self.pending_commands: Dict[str, asyncio.Future] = {}
        
        # Event handlers
        self.event_handlers: Dict[str, List[Callable]] = {}
        
        # Connection status callbacks
        self.on_connect_callbacks: List[Callable] = []
        self.on_disconnect_callbacks: List[Callable] = []
        
        # Create tasks set to keep track of running tasks
        self.tasks: Set[asyncio.Task] = set()
    
    async def connect(self) -> bool:
        """Connect to the WhatsApp Gateway."""
        if self.connected:
            return True
        
        try:
            logger.info(f"Connecting to WhatsApp Gateway at {self.ws_url}")
            # Using websockets library directly
            self.websocket = await websockets.connect(
                self.ws_url,
                ping_interval=30,
                ping_timeout=10,
                close_timeout=5,
            )
            self.connected = True
            
            # Start message receiver task
            self.receive_task = asyncio.create_task(self._receive_messages())
            self.tasks.add(self.receive_task)
            self.receive_task.add_done_callback(self.tasks.discard)
            
            # Notify connection callbacks
            for callback in self.on_connect_callbacks:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback()
                    else:
                        callback()
                except Exception as e:
                    logger.error(f"Error in connect callback: {e}")
            
            logger.info("Connected to WhatsApp Gateway")
            return True
        except (WebSocketException, OSError) as e:
            logger.error(f"Failed to connect to WhatsApp Gateway: {e}")
            self.connected = False
            
            # Start reconnection task if not already running
            if not self.reconnect_task or self.reconnect_task.done():
                self.reconnect_task = asyncio.create_task(self._reconnect())
                self.tasks.add(self.reconnect_task)
                self.reconnect_task.add_done_callback(self.tasks.discard)
            
            return False
    
    async def disconnect(self) -> None:
        """Disconnect from the WhatsApp Gateway."""
        self.connected = False
        
        # Cancel running tasks
        for task in self.tasks:
            task.cancel()
        
        # Close WebSocket connection
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
        
        # Notify disconnection callbacks
        for callback in self.on_disconnect_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback()
                else:
                    callback()
            except Exception as e:
                logger.error(f"Error in disconnect callback: {e}")
        
        logger.info("Disconnected from WhatsApp Gateway")
    
    def is_connected(self) -> bool:
        """Check if the client is connected to the WhatsApp Gateway."""
        return self.connected and self.websocket is not None
    
    def is_authenticated(self) -> bool:
        """Check if the client is authenticated with WhatsApp."""
        return self.authenticated
    
    async def send_command(
        self,
        command: str,
        data: Optional[Dict[str, Any]] = None,
        timeout: int = 30,
    ) -> Dict[str, Any]:
        """Send a command to the WhatsApp Gateway and wait for the response."""
        if not self.is_connected():
            raise ConnectionError("Not connected to WhatsApp Gateway")
        
        # Generate command ID
        command_id = str(uuid.uuid4())
        
        # Create message
        message = {
            "type": "command",
            "id": command_id,
            "command": command,
            "data": data or {},
            "timestamp": None,  # Server will set this
        }
        
        # Create future for response
        future = asyncio.Future()
        self.pending_commands[command_id] = future
        
        try:
            # Send command
            await self.websocket.send(json.dumps(message))
            
            # Wait for response with timeout
            return await asyncio.wait_for(future, timeout)
        except asyncio.TimeoutError:
            logger.error(f"Command {command} timed out after {timeout} seconds")
            self.pending_commands.pop(command_id, None)
            raise TimeoutError(f"Command {command} timed out")
        except WebSocketException as e:
            logger.error(f"WebSocket error sending command {command}: {e}")
            self.pending_commands.pop(command_id, None)
            raise ConnectionError(f"WebSocket error: {str(e)}")
        except Exception as e:
            logger.error(f"Error sending command {command}: {e}")
            self.pending_commands.pop(command_id, None)
            raise
    
    def register_event_handler(self, event: str, handler: Callable) -> None:
        """Register a handler for a specific event."""
        if event not in self.event_handlers:
            self.event_handlers[event] = []
        
        self.event_handlers[event].append(handler)
    
    def unregister_event_handler(self, event: str, handler: Callable) -> None:
        """Unregister a handler for a specific event."""
        if event in self.event_handlers:
            try:
                self.event_handlers[event].remove(handler)
            except ValueError:
                pass
    
    def on_connect(self, callback: Callable) -> None:
        """Register a callback for connection events."""
        self.on_connect_callbacks.append(callback)
    
    def on_disconnect(self, callback: Callable) -> None:
        """Register a callback for disconnection events."""
        self.on_disconnect_callbacks.append(callback)
    
    async def _receive_messages(self) -> None:
        """Receive messages from the WebSocket connection."""
        if not self.websocket:
            return
        
        try:
            async for message in self.websocket:
                try:
                    # Parse message
                    data = json.loads(message)
                    message_type = data.get("type")
                    
                    if message_type == "response":
                        # Handle command response
                        command_id = data.get("id")
                        if command_id in self.pending_commands:
                            future = self.pending_commands.pop(command_id)
                            if not future.done():
                                future.set_result(data)
                    
                    elif message_type == "error":
                        # Handle command error
                        command_id = data.get("id")
                        if command_id in self.pending_commands:
                            future = self.pending_commands.pop(command_id)
                            if not future.done():
                                future.set_exception(Exception(data.get("error", "Unknown error")))
                    
                    elif message_type == "event":
                        # Handle events
                        event_type = data.get("event")
                        if event_type:
                            # Update authentication status
                            if event_type == "authenticated":
                                self.authenticated = True
                            elif event_type == "disconnected":
                                self.authenticated = False
                            
                            # Call event handlers
                            await self._dispatch_event(event_type, data)
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse message: {message}")
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
        except ConnectionClosed:
            logger.warning("WebSocket connection closed")
            self.connected = False
            
            # Reject pending commands
            for command_id, future in self.pending_commands.items():
                if not future.done():
                    future.set_exception(ConnectionError("Connection closed"))
            self.pending_commands.clear()
            
            # Start reconnection task if not already running
            if not self.reconnect_task or self.reconnect_task.done():
                self.reconnect_task = asyncio.create_task(self._reconnect())
                self.tasks.add(self.reconnect_task)
                self.reconnect_task.add_done_callback(self.tasks.discard)
        except Exception as e:
            logger.error(f"Error in message receiver: {e}")
            self.connected = False
    
    async def _reconnect(self) -> None:
        """Reconnect to the WhatsApp Gateway."""
        attempt = 0
        
        while attempt < self.max_reconnect_attempts and not self.connected:
            attempt += 1
            logger.info(f"Reconnecting to WhatsApp Gateway (attempt {attempt}/{self.max_reconnect_attempts})")
            
            try:
                await asyncio.sleep(self.reconnect_interval)
                await self.connect()
                
                if self.connected:
                    logger.info(f"Reconnected to WhatsApp Gateway after {attempt} attempts")
                    return
            except Exception as e:
                logger.error(f"Reconnection attempt {attempt} failed: {e}")
        
        if not self.connected:
            logger.error(f"Failed to reconnect after {self.max_reconnect_attempts} attempts")
    
    async def _dispatch_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Dispatch an event to registered handlers."""
        if event_type in self.event_handlers:
            for handler in self.event_handlers[event_type]:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(data)
                    else:
                        handler(data)
                except Exception as e:
                    logger.error(f"Error in event handler for {event_type}: {e}")