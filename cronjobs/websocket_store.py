from fastapi import WebSocket
from typing import Dict
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("websocket_store")

# Store active WebSocket connections
active_connections: Dict[str, WebSocket] = {}

def register_websocket(socket_id: str, websocket: WebSocket):
    """Register a WebSocket connection"""
    active_connections[socket_id] = websocket
    logger.debug(f"Registered WebSocket connection: {socket_id}")

def remove_websocket(socket_id: str):
    """Remove a WebSocket connection"""
    if socket_id in active_connections:
        del active_connections[socket_id]
        logger.debug(f"Removed WebSocket connection: {socket_id}")

def get_websocket(socket_id: str) -> WebSocket:
    """Get a WebSocket connection by socket_id"""
    return active_connections.get(socket_id) 