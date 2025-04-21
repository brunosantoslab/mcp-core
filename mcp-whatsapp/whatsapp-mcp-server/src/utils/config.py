"""
Configuration module for the MCP WhatsApp Server.

@author Bruno Santos
"""

import os
import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config(BaseModel):
    """Configuration model for the MCP WhatsApp Server."""
    
    # Server configuration
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8080)
    debug: bool = Field(default=False)
    log_level: str = Field(default="INFO")
    
    # WhatsApp Gateway configuration
    gateway_host: str = Field(default="localhost")
    gateway_port: int = Field(default=8090)
    gateway_path: str = Field(default="/ws")
    reconnect_interval: int = Field(default=5)
    max_reconnect_attempts: int = Field(default=10)
    
    # Security configuration
    allowed_origins: List[str] = Field(default=["*"])
    
    # Cache configuration
    cache_dir: str = Field(default="./cache")
    cache_ttl: int = Field(default=86400)  # 24 hours in seconds
    
    # Media configuration
    media_dir: str = Field(default="./media")
    media_ttl: int = Field(default=604800)  # 7 days in seconds
    max_media_size: int = Field(default=10485760)  # 10MB in bytes
    
    class Config:
        """Pydantic configuration."""
        
        env_prefix = "MCP_"
        env_file = ".env"
        env_file_encoding = "utf-8"
        
        # Allow extra fields in the config file
        extra = "allow"

def load_config(config_path: Optional[str] = None) -> Config:
    """Load configuration from environment variables and config file."""
    
    # Try to load from config file if provided
    config_data: Dict[str, Any] = {}
    if config_path:
        config_file = Path(config_path)
        if config_file.exists():
            with open(config_file, "r") as f:
                config_data = json.load(f)
    
    # Check for claude desktop config
    claude_config_path = os.environ.get("CLAUDE_CONFIG_PATH", "")
    if claude_config_path and not config_path:
        claude_config_file = Path(claude_config_path)
        if claude_config_file.exists():
            try:
                with open(claude_config_file, "r") as f:
                    claude_config = json.load(f)
                    
                # Extract WhatsApp plugin configuration
                if "mcp" in claude_config and "plugins" in claude_config["mcp"]:
                    for plugin in claude_config["mcp"]["plugins"]:
                        if plugin.get("name") == "whatsapp" and plugin.get("enabled"):
                            if "server" in plugin:
                                server_config = plugin["server"]
                                config_data["host"] = server_config.get("host", config_data.get("host"))
                                config_data["port"] = server_config.get("port", config_data.get("port"))
                            
                            if "settings" in plugin:
                                settings = plugin["settings"]
                                if "cacheDirectory" in settings:
                                    config_data["cache_dir"] = settings["cacheDirectory"]
                                if "cacheTTL" in settings:
                                    config_data["cache_ttl"] = settings["cacheTTL"]
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading Claude config: {e}")
    
    # Create configuration, environment variables will override config file values
    config = Config(**config_data)
    
    # Create directories if they don't exist
    Path(config.cache_dir).mkdir(parents=True, exist_ok=True)
    Path(config.media_dir).mkdir(parents=True, exist_ok=True)
    
    return config
