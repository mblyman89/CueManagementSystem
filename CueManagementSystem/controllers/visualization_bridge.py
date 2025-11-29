"""
Visualization Bridge Controller
================================

WebSocket-based communication bridge between Python CueManagementSystem
and Unreal Engine 5 for real-time firework visualization.

Features:
- WebSocket server/client for UE5 communication
- JSON message serialization
- Command queue for reliable delivery
- Connection management and monitoring
- Event-based architecture
- Error handling and logging

Author: Michael Lyman
Version: 1.0.0
License: MIT
"""

import asyncio
import json
import logging
import time
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass
from enum import Enum
import websockets
from websockets.server import WebSocketServerProtocol
from queue import Queue
import threading

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConnectionState(Enum):
    """WebSocket connection states"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    LISTENING = "listening"
    CONNECTED = "connected"
    ERROR = "error"


class MessageType(Enum):
    """Message types for UE5 communication"""
    # Firework Commands
    LAUNCH_FIREWORK = "launch_firework"
    BATCH_LAUNCH = "batch_launch"

    # Environment Commands
    UPDATE_ENVIRONMENT = "update_environment"
    SET_CAMERA = "set_camera"
    SET_WEATHER = "set_weather"

    # Synchronization
    SYNC_TIME = "sync_time"
    HEARTBEAT = "heartbeat"

    # Control
    PAUSE = "pause"
    RESUME = "resume"
    STOP = "stop"
    RESET = "reset"

    # Status
    STATUS_REQUEST = "status_request"
    STATUS_RESPONSE = "status_response"


@dataclass
class VisualizationMessage:
    """Message structure for UE5 communication"""
    message_type: str
    timestamp: float
    data: Dict[str, Any]
    message_id: Optional[str] = None

    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps({
            "type": self.message_type,
            "timestamp": self.timestamp,
            "data": self.data,
            "id": self.message_id
        })

    @classmethod
    def from_json(cls, json_str: str) -> 'VisualizationMessage':
        """Create from JSON string"""
        data = json.loads(json_str)
        return cls(
            message_type=data.get("type"),
            timestamp=data.get("timestamp", time.time()),
            data=data.get("data", {}),
            message_id=data.get("id")
        )


class VisualizationBridge:
    """
    WebSocket bridge for Python-to-UE5 communication

    This class manages the connection to Unreal Engine 5 and handles
    sending visualization commands in real-time.
    """

    def __init__(self, host: str = "localhost", port: int = 8765):
        """
        Initialize the visualization bridge

        Args:
            host: WebSocket server host
            port: WebSocket server port
        """
        self.host = host
        self.port = port
        self.connection_state = ConnectionState.DISCONNECTED

        # WebSocket connection
        self.websocket: Optional[WebSocketServerProtocol] = None
        self.server = None
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.server_thread: Optional[threading.Thread] = None

        # Message queue
        self.message_queue: Queue = Queue()
        self.send_thread: Optional[threading.Thread] = None
        self.running = False

        # Callbacks
        self.on_connected: Optional[Callable] = None
        self.on_disconnected: Optional[Callable] = None
        self.on_message_received: Optional[Callable[[Dict], None]] = None
        self.on_error: Optional[Callable[[Exception], None]] = None

        # Statistics
        self.messages_sent = 0
        self.messages_received = 0
        self.last_heartbeat = 0

        logger.info(f"VisualizationBridge initialized on {host}:{port}")

    def start_server(self) -> bool:
        """
        Start the WebSocket server in a separate thread

        Returns:
            bool: True if server started successfully
        """
        try:
            self.running = True
            self.server_thread = threading.Thread(target=self._run_server, daemon=True)
            self.server_thread.start()

            # Start message sender thread
            self.send_thread = threading.Thread(target=self._process_message_queue, daemon=True)
            self.send_thread.start()

            # Give the server thread a moment to initialize
            import time
            time.sleep(0.5)

            logger.info("WebSocket server started")
            return True

        except Exception as e:
            logger.error(f"Failed to start server: {e}")
            import traceback
            traceback.print_exc()
            if self.on_error:
                self.on_error(e)
            return False

    def stop_server(self):
        """Stop the WebSocket server"""
        self.running = False

        if self.loop and self.server:
            asyncio.run_coroutine_threadsafe(self.server.close(), self.loop)

        if self.server_thread:
            self.server_thread.join(timeout=2.0)

        if self.send_thread:
            self.send_thread.join(timeout=2.0)

        self.connection_state = ConnectionState.DISCONNECTED
        logger.info("WebSocket server stopped")

    def _run_server(self):
        """Run the WebSocket server (internal)"""
        try:
            # Create new event loop for this thread
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)

            # Define async function to start server
            async def start_server():
                return await websockets.serve(self._handle_client, self.host, self.port)

            # Start the WebSocket server
            self.server = self.loop.run_until_complete(start_server())
            logger.info(f"WebSocket server listening on ws://{self.host}:{self.port}")

            # Update connection state to listening
            self.connection_state = ConnectionState.LISTENING

            # Run the event loop forever
            self.loop.run_forever()

        except Exception as e:
            logger.error(f"Server error: {e}")
            import traceback
            traceback.print_exc()
            if self.on_error:
                self.on_error(e)
        finally:
            # Clean up
            if self.server:
                self.server.close()
                self.loop.run_until_complete(self.server.wait_closed())
            self.loop.close()

    async def _handle_client(self, websocket: WebSocketServerProtocol):
        """
        Handle incoming WebSocket client connection

        Args:
            websocket: WebSocket connection
        """
        self.websocket = websocket
        self.connection_state = ConnectionState.CONNECTED

        logger.info(f"Client connected from {websocket.remote_address}")

        if self.on_connected:
            self.on_connected()

        try:
            async for message in websocket:
                await self._handle_message(message)

        except websockets.exceptions.ConnectionClosed:
            logger.info("Client disconnected")
        except Exception as e:
            logger.error(f"Error handling client: {e}")
            if self.on_error:
                self.on_error(e)
        finally:
            self.websocket = None
            self.connection_state = ConnectionState.DISCONNECTED
            if self.on_disconnected:
                self.on_disconnected()

    async def _handle_message(self, message: str):
        """
        Handle incoming message from UE5

        Args:
            message: JSON message string
        """
        try:
            msg = VisualizationMessage.from_json(message)
            self.messages_received += 1

            logger.debug(f"Received message: {msg.message_type}")

            # Handle specific message types
            if msg.message_type == MessageType.HEARTBEAT.value:
                self.last_heartbeat = time.time()
                # Send heartbeat response
                await self._send_immediate({
                    "type": MessageType.HEARTBEAT.value,
                    "timestamp": time.time()
                })

            elif msg.message_type == MessageType.STATUS_REQUEST.value:
                # Send status response
                await self._send_immediate(self._get_status())

            # Notify callback
            if self.on_message_received:
                self.on_message_received(msg.data)

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON received: {e}")
        except Exception as e:
            logger.error(f"Error processing message: {e}")

    async def _send_immediate(self, data: Dict[str, Any]):
        """
        Send message immediately (internal)

        Args:
            data: Message data dictionary
        """
        if self.websocket and self.connection_state == ConnectionState.CONNECTED:
            try:
                await self.websocket.send(json.dumps(data))
                self.messages_sent += 1
            except Exception as e:
                logger.error(f"Error sending message: {e}")

    def _process_message_queue(self):
        """Process queued messages (runs in separate thread)"""
        while self.running:
            try:
                if not self.message_queue.empty():
                    message = self.message_queue.get(timeout=0.1)

                    if self.websocket and self.connection_state == ConnectionState.CONNECTED:
                        # Send message in the event loop
                        future = asyncio.run_coroutine_threadsafe(
                            self._send_immediate(message),
                            self.loop
                        )
                        future.result(timeout=1.0)
                    else:
                        logger.warning("Cannot send message: not connected")
                else:
                    time.sleep(0.01)  # Small sleep to prevent busy waiting

            except Exception as e:
                logger.error(f"Error processing message queue: {e}")

    def send_launch_command(self, cue_data: Dict[str, Any]):
        """
        Send firework launch command to UE5

        Args:
            cue_data: Cue visualization data
        """
        message = {
            "type": MessageType.LAUNCH_FIREWORK.value,
            "timestamp": time.time(),
            "data": cue_data
        }
        self.message_queue.put(message)
        logger.debug(f"Queued launch command for cue {cue_data.get('cue_number')}")

    def send_batch_launch(self, cues: List[Dict[str, Any]]):
        """
        Send multiple firework launch commands at once

        Args:
            cues: List of cue visualization data
        """
        message = {
            "type": MessageType.BATCH_LAUNCH.value,
            "timestamp": time.time(),
            "data": {"cues": cues}
        }
        self.message_queue.put(message)
        logger.info(f"Queued batch launch with {len(cues)} cues")

    def update_environment(self, environment_data: Dict[str, Any]):
        """
        Update UE5 environment settings

        Args:
            environment_data: Environment configuration
                - time_of_day: float (0-24)
                - weather: str ("clear", "foggy", "windy")
                - wind_speed: float
                - wind_direction: float (degrees)
        """
        message = {
            "type": MessageType.UPDATE_ENVIRONMENT.value,
            "timestamp": time.time(),
            "data": environment_data
        }
        self.message_queue.put(message)
        logger.info("Queued environment update")

    def set_camera(self, camera_data: Dict[str, Any]):
        """
        Set camera position and settings

        Args:
            camera_data: Camera configuration
                - position: {x, y, z}
                - rotation: {pitch, yaw, roll}
                - fov: float
        """
        message = {
            "type": MessageType.SET_CAMERA.value,
            "timestamp": time.time(),
            "data": camera_data
        }
        self.message_queue.put(message)

    def sync_time(self, show_time: float):
        """
        Synchronize time with UE5

        Args:
            show_time: Current show time in seconds
        """
        message = {
            "type": MessageType.SYNC_TIME.value,
            "timestamp": time.time(),
            "data": {"show_time": show_time}
        }
        self.message_queue.put(message)

    def pause(self):
        """Pause visualization"""
        message = {
            "type": MessageType.PAUSE.value,
            "timestamp": time.time(),
            "data": {}
        }
        self.message_queue.put(message)
        logger.info("Sent pause command")

    def resume(self):
        """Resume visualization"""
        message = {
            "type": MessageType.RESUME.value,
            "timestamp": time.time(),
            "data": {}
        }
        self.message_queue.put(message)
        logger.info("Sent resume command")

    def stop(self):
        """Stop visualization"""
        message = {
            "type": MessageType.STOP.value,
            "timestamp": time.time(),
            "data": {}
        }
        self.message_queue.put(message)
        logger.info("Sent stop command")

    def reset(self):
        """Reset visualization to initial state"""
        message = {
            "type": MessageType.RESET.value,
            "timestamp": time.time(),
            "data": {}
        }
        self.message_queue.put(message)
        logger.info("Sent reset command")

    def _get_status(self) -> Dict[str, Any]:
        """Get current bridge status"""
        return {
            "type": MessageType.STATUS_RESPONSE.value,
            "timestamp": time.time(),
            "data": {
                "connection_state": self.connection_state.value,
                "messages_sent": self.messages_sent,
                "messages_received": self.messages_received,
                "queue_size": self.message_queue.qsize(),
                "last_heartbeat": self.last_heartbeat
            }
        }

    def is_connected(self) -> bool:
        """Check if connected to UE5"""
        return self.connection_state == ConnectionState.CONNECTED

    def get_statistics(self) -> Dict[str, Any]:
        """Get connection statistics"""
        return {
            "state": self.connection_state.value,
            "messages_sent": self.messages_sent,
            "messages_received": self.messages_received,
            "queue_size": self.message_queue.qsize(),
            "last_heartbeat": self.last_heartbeat,
            "uptime": time.time() - self.last_heartbeat if self.last_heartbeat > 0 else 0
        }


# Example usage
if __name__ == "__main__":
    # Create bridge
    bridge = VisualizationBridge(host="localhost", port=8765)


    # Set up callbacks
    def on_connected():
        print("✓ Connected to UE5")


    def on_disconnected():
        print("✗ Disconnected from UE5")


    def on_message(data):
        print(f"← Received: {data}")


    bridge.on_connected = on_connected
    bridge.on_disconnected = on_disconnected
    bridge.on_message_received = on_message

    # Start server
    if bridge.start_server():
        print(f"WebSocket server running on ws://{bridge.host}:{bridge.port}")
        print("Waiting for UE5 to connect...")

        try:
            # Keep running
            while True:
                time.sleep(1)

                # Send test command every 5 seconds if connected
                if bridge.is_connected() and int(time.time()) % 5 == 0:
                    test_cue = {
                        "cue_number": 1,
                        "effect": {
                            "type": "gold_peony",
                            "color": {"r": 255, "g": 215, "b": 0}
                        },
                        "position": {"x": 0, "y": 0, "z": 0}
                    }
                    bridge.send_launch_command(test_cue)
                    print(f"→ Sent test command")

        except KeyboardInterrupt:
            print("\nShutting down...")
            bridge.stop_server()