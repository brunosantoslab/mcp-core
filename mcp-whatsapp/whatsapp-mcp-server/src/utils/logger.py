"""
Logger configuration for the MCP WhatsApp Server.

@author Bruno Santos
"""

import os
import sys
from pathlib import Path
from loguru import logger

# Remove default handler
logger.remove()

# Determine log level from environment variable
log_level = os.environ.get("MCP_LOG_LEVEL", "INFO").upper()

# Set up console logging
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level=log_level,
    colorize=True,
)

# Create logs directory if it doesn't exist
logs_dir = Path(os.environ.get("MCP_LOG_DIR", "./logs"))
logs_dir.mkdir(parents=True, exist_ok=True)

# Set up file logging
logger.add(
    logs_dir / "mcp-server.log",
    format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
    level=log_level,
    rotation="10 MB",  # Rotate when file reaches 10MB
    compression="zip",  # Compress rotated files
    retention="1 week",  # Keep logs for 1 week
)

def get_logger(name):
    """Get a logger with the given name."""
    return logger.bind(name=name)
