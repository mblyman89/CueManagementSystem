"""
Professional MQTT Client for Firework Show Control System

This module provides a robust, thread-safe MQTT client specifically designed
for safety-critical firework control applications with the following features:

- QoS 2 (exactly-once delivery) for critical commands
- SSL/TLS encryption for secure communication
- Automatic reconnection with exponential backoff
- Message queuing for offline scenarios
- Comprehensive error handling and logging
- Thread-safe operations
- Connection health monitoring
- Emergency stop functionality
"""

import asyncio
import json
import logging
import ssl
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from queue import Queue, Empty
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime, timedelta

import paho.mqtt.client as mqtt
from PySide6.QtCore import QObject, Signal, QTimer, QThread


class ConnectionState(Enum):
    """MQTT connection states"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    ERROR = "error"


class MessagePriority(Enum):
    """Message priority levels"""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3  # For emergency stop and safety commands


@dataclass
class MQTTMessage:
    """MQTT message with metadata"""
    topic: str
    payload: bytes
    qos: int = 2  # Default to QoS 2 for safety-critical applications
    retain: bool = False
    priority: MessagePriority = MessagePriority.NORMAL
    timestamp: datetime = field(default_factory=datetime.now)
    retry_count: int = 0
    max_retries: int = 3
    message_id: Optional[str] = None


@dataclass
class ConnectionConfig:
    """MQTT connection configuration"""
    host: str = "raspberrypi.local"
    port: int = 8883  # Default to secure port
    username: Optional[str] = None
    password: Optional[str] = None
    client_id: Optional[str] = None

    # SSL/TLS Configuration
    use_ssl: bool = False  # Default to False for basic MQTT connections
    ca_cert_path: Optional[str] = None
    cert_file_path: Optional[str] = None
    key_file_path: Optional[str] = None
    insecure: bool = False  # Set to True to skip certificate verification (NOT recommended for production)

    # Connection Parameters
    keepalive: int = 60
    clean_session: bool = False  # Use persistent sessions for reliability
    reconnect_delay_min: float = 1.0
    reconnect_delay_max: float = 60.0
    max_reconnect_attempts: int = -1  # -1 for infinite attempts

    # Topic Configuration
    base_topic: str = "fireworks"
    command_topic: str = "commands"
    status_topic: str = "status"
    emergency_topic: str = "emergency"
    heartbeat_topic: str = "heartbeat"

    # Quality of Service Settings
    default_qos: int = 2  # Exactly-once delivery for safety
    emergency_qos: int = 2  # Critical commands must use QoS 2
    status_qos: int = 1  # Status updates can use QoS 1

    # Message Settings
    message_timeout: float = 30.0
    heartbeat_interval: float = 10.0
    max_queued_messages: int = 1000


class MQTTClient(QObject):
    """
    Professional MQTT client for firework show control

    Features:
    - Thread-safe operations
    - Automatic reconnection with exponential backoff
    - Message queuing and prioritization
    - SSL/TLS support
    - Connection health monitoring
    - Emergency stop functionality
    - Comprehensive logging
    """

    # Qt Signals for UI updates
    connection_state_changed = Signal(ConnectionState)
    message_received = Signal(str, bytes)  # topic, payload
    message_sent = Signal(str, bytes)  # topic, payload
    error_occurred = Signal(str)  # error message
    connection_quality_changed = Signal(float)  # quality percentage (0-100)

    def __init__(self, config: ConnectionConfig, parent=None):
        super().__init__(parent)

        self.config = config
        self.logger = self._setup_logging()

        # Connection state
        self._state = ConnectionState.DISCONNECTED
        self._client: Optional[mqtt.Client] = None
        self._connection_thread: Optional[QThread] = None
        self._reconnect_attempts = 0
        self._last_heartbeat = datetime.now()

        # Message handling
        self._message_queue = Queue(maxsize=config.max_queued_messages)
        self._pending_messages: Dict[int, MQTTMessage] = {}
        self._message_lock = threading.Lock()

        # Timers
        self._heartbeat_timer = QTimer()
        self._heartbeat_timer.timeout.connect(self._send_heartbeat)
        self._connection_monitor_timer = QTimer()
        self._connection_monitor_timer.timeout.connect(self._monitor_connection)

        # Statistics
        self._stats = {
            'messages_sent': 0,
            'messages_received': 0,
            'connection_attempts': 0,
            'last_error': None,
            'uptime_start': None
        }

        self.logger.info("MQTT Client initialized")

    def _setup_logging(self) -> logging.Logger:
        """Setup logging for MQTT client"""
        logger = logging.getLogger(f"MQTTClient_{id(self)}")
        logger.setLevel(logging.DEBUG)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    @property
    def state(self) -> ConnectionState:
        """Get current connection state"""
        return self._state

    @property
    def is_connected(self) -> bool:
        """Check if client is connected"""
        return self._state == ConnectionState.CONNECTED

    @property
    def statistics(self) -> Dict[str, Any]:
        """Get connection statistics"""
        stats = self._stats.copy()
        if stats['uptime_start']:
            stats['uptime'] = (datetime.now() - stats['uptime_start']).total_seconds()
        return stats

    def connect(self) -> bool:
        """
        Connect to MQTT broker

        Returns:
            bool: True if connection initiated successfully
        """
        if self._state in [ConnectionState.CONNECTING, ConnectionState.CONNECTED]:
            self.logger.warning("Already connected or connecting")
            return True

        try:
            self._set_state(ConnectionState.CONNECTING)
            self._stats['connection_attempts'] += 1

            # Create MQTT client
            client_id = self.config.client_id or f"fireworks_control_{int(time.time())}"
            self._client = mqtt.Client(
                client_id=client_id,
                clean_session=self.config.clean_session,
                protocol=mqtt.MQTTv311
            )

            # Set callbacks
            self._client.on_connect = self._on_connect
            self._client.on_disconnect = self._on_disconnect
            self._client.on_message = self._on_message
            self._client.on_publish = self._on_publish
            self._client.on_subscribe = self._on_subscribe
            self._client.on_log = self._on_log

            # Configure authentication
            if self.config.username and self.config.password:
                self._client.username_pw_set(self.config.username, self.config.password)

            # Configure SSL/TLS
            if self.config.use_ssl:
                self._configure_ssl()

            # Start connection
            self.logger.info(f"Connecting to {self.config.host}:{self.config.port}")
            self._client.connect_async(
                self.config.host,
                self.config.port,
                self.config.keepalive
            )

            # Start network loop in separate thread
            self._client.loop_start()

            return True

        except Exception as e:
            self.logger.error(f"Connection failed: {e}")
            self._set_state(ConnectionState.ERROR)
            self.error_occurred.emit(str(e))
            return False

    def disconnect(self):
        """Disconnect from MQTT broker"""
        if self._client and self._state != ConnectionState.DISCONNECTED:
            self.logger.info("Disconnecting from MQTT broker")
            self._client.disconnect()
            self._client.loop_stop()
            self._set_state(ConnectionState.DISCONNECTED)

    def publish(self, topic: str, payload: Any, qos: Optional[int] = None,
                retain: bool = False, priority: MessagePriority = MessagePriority.NORMAL) -> bool:
        """
        Publish message to MQTT broker

        Args:
            topic: MQTT topic
            payload: Message payload (will be JSON encoded if not bytes/str)
            qos: Quality of Service level (defaults to config default)
            retain: Retain message flag
            priority: Message priority

        Returns:
            bool: True if message queued successfully
        """
        try:
            # Prepare payload
            if isinstance(payload, (dict, list)):
                payload_bytes = json.dumps(payload).encode('utf-8')
            elif isinstance(payload, str):
                payload_bytes = payload.encode('utf-8')
            elif isinstance(payload, bytes):
                payload_bytes = payload
            else:
                payload_bytes = str(payload).encode('utf-8')

            # Create message
            message = MQTTMessage(
                topic=topic,
                payload=payload_bytes,
                qos=qos or self.config.default_qos,
                retain=retain,
                priority=priority,
                message_id=f"{topic}_{int(time.time() * 1000)}"
            )

            # Queue message
            if self._message_queue.full():
                self.logger.warning("Message queue full, dropping oldest message")
                try:
                    self._message_queue.get_nowait()
                except Empty:
                    pass

            self._message_queue.put(message)
            self._process_message_queue()

            return True

        except Exception as e:
            self.logger.error(f"Failed to publish message: {e}")
            self.error_occurred.emit(f"Publish failed: {e}")
            return False

    def subscribe(self, topic: str, qos: int = 2) -> bool:
        """
        Subscribe to MQTT topic

        Args:
            topic: MQTT topic to subscribe to
            qos: Quality of Service level

        Returns:
            bool: True if subscription initiated successfully
        """
        if not self.is_connected:
            self.logger.warning("Cannot subscribe: not connected")
            return False

        try:
            result, mid = self._client.subscribe(topic, qos)
            if result == mqtt.MQTT_ERR_SUCCESS:
                self.logger.info(f"Subscribed to topic: {topic} (QoS {qos})")
                return True
            else:
                self.logger.error(f"Subscription failed: {mqtt.error_string(result)}")
                return False

        except Exception as e:
            self.logger.error(f"Subscription error: {e}")
            return False

    def emergency_stop(self) -> bool:
        """
        Send emergency stop command with highest priority

        Returns:
            bool: True if emergency stop sent successfully
        """
        emergency_payload = {
            'command': 'EMERGENCY_STOP',
            'timestamp': datetime.now().isoformat(),
            'source': 'control_application'
        }

        topic = f"{self.config.base_topic}/{self.config.emergency_topic}"

        return self.publish(
            topic=topic,
            payload=emergency_payload,
            qos=self.config.emergency_qos,
            priority=MessagePriority.CRITICAL
        )

    def send_cue_command(self, cue_data: Dict[str, Any]) -> bool:
        """
        Send firework cue command

        Args:
            cue_data: Cue data dictionary

        Returns:
            bool: True if command sent successfully
        """
        # Add metadata to cue data
        command_payload = {
            'type': 'CUE_COMMAND',
            'cue_data': cue_data,
            'timestamp': datetime.now().isoformat(),
            'source': 'control_application'
        }

        topic = f"{self.config.base_topic}/{self.config.command_topic}"

        return self.publish(
            topic=topic,
            payload=command_payload,
            qos=self.config.default_qos,
            priority=MessagePriority.HIGH
        )

    def _configure_ssl(self):
        """Configure SSL/TLS settings"""
        try:
            context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)

            if self.config.ca_cert_path:
                context.load_verify_locations(self.config.ca_cert_path)

            if self.config.cert_file_path and self.config.key_file_path:
                context.load_cert_chain(self.config.cert_file_path, self.config.key_file_path)

            if self.config.insecure:
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                self.logger.warning("SSL certificate verification disabled - NOT recommended for production")

            self._client.tls_set_context(context)
            self.logger.info("SSL/TLS configured")

        except Exception as e:
            self.logger.error(f"SSL configuration failed: {e}")
            raise

    def _set_state(self, new_state: ConnectionState):
        """Update connection state and emit signal"""
        if self._state != new_state:
            old_state = self._state
            self._state = new_state
            self.logger.info(f"State changed: {old_state.value} -> {new_state.value}")
            self.connection_state_changed.emit(new_state)

            if new_state == ConnectionState.CONNECTED:
                self._stats['uptime_start'] = datetime.now()
                self._start_heartbeat()
                self._start_connection_monitoring()
            elif new_state == ConnectionState.DISCONNECTED:
                self._stop_heartbeat()
                self._stop_connection_monitoring()

    def _process_message_queue(self):
        """Process queued messages"""
        if not self.is_connected:
            return

        messages_to_send = []

        # Get messages from queue (prioritized)
        while not self._message_queue.empty() and len(messages_to_send) < 10:
            try:
                message = self._message_queue.get_nowait()
                messages_to_send.append(message)
            except Empty:
                break

        # Sort by priority
        messages_to_send.sort(key=lambda m: m.priority.value, reverse=True)

        # Send messages
        for message in messages_to_send:
            self._send_message(message)

    def _send_message(self, message: MQTTMessage):
        """Send individual message"""
        try:
            with self._message_lock:
                result = self._client.publish(
                    message.topic,
                    message.payload,
                    message.qos,
                    message.retain
                )

                if result.rc == mqtt.MQTT_ERR_SUCCESS:
                    self._pending_messages[result.mid] = message
                    self._stats['messages_sent'] += 1
                    self.logger.debug(f"Message sent: {message.topic}")
                else:
                    self.logger.error(f"Failed to send message: {mqtt.error_string(result.rc)}")

        except Exception as e:
            self.logger.error(f"Error sending message: {e}")

    def _start_heartbeat(self):
        """Start heartbeat timer"""
        self._heartbeat_timer.start(int(self.config.heartbeat_interval * 1000))

    def _stop_heartbeat(self):
        """Stop heartbeat timer"""
        self._heartbeat_timer.stop()

    def _send_heartbeat(self):
        """Send heartbeat message"""
        heartbeat_payload = {
            'timestamp': datetime.now().isoformat(),
            'client_id': self._client._client_id.decode() if self._client else 'unknown',
            'stats': self.statistics
        }

        topic = f"{self.config.base_topic}/{self.config.heartbeat_topic}"
        self.publish(topic, heartbeat_payload, qos=0, priority=MessagePriority.LOW)
        self._last_heartbeat = datetime.now()

    def _start_connection_monitoring(self):
        """Start connection monitoring"""
        self._connection_monitor_timer.start(5000)  # Check every 5 seconds

    def _stop_connection_monitoring(self):
        """Stop connection monitoring"""
        self._connection_monitor_timer.stop()

    def _monitor_connection(self):
        """Monitor connection health"""
        if not self.is_connected:
            return

        # Check heartbeat timeout
        time_since_heartbeat = (datetime.now() - self._last_heartbeat).total_seconds()
        if time_since_heartbeat > self.config.heartbeat_interval * 3:
            self.logger.warning("Heartbeat timeout detected")
            self.connection_quality_changed.emit(0.0)
        else:
            # Calculate connection quality based on various factors
            quality = min(100.0, max(0.0, 100.0 - (time_since_heartbeat / self.config.heartbeat_interval) * 10))
            self.connection_quality_changed.emit(quality)

    # MQTT Callbacks
    def _on_connect(self, client, userdata, flags, rc):
        """Handle MQTT connection"""
        if rc == 0:
            self.logger.info("Connected to MQTT broker")
            self._set_state(ConnectionState.CONNECTED)
            self._reconnect_attempts = 0

            # Subscribe to default topics
            self.subscribe(f"{self.config.base_topic}/{self.config.status_topic}/#")
            self.subscribe(f"{self.config.base_topic}/{self.config.emergency_topic}")

        else:
            self.logger.error(f"Connection failed with code {rc}: {mqtt.connack_string(rc)}")
            self._set_state(ConnectionState.ERROR)
            self.error_occurred.emit(f"Connection failed: {mqtt.connack_string(rc)}")

    def _on_disconnect(self, client, userdata, rc):
        """Handle MQTT disconnection"""
        if rc != 0:
            self.logger.warning(f"Unexpected disconnection (code {rc})")
            self._set_state(ConnectionState.RECONNECTING)
            self._schedule_reconnect()
        else:
            self.logger.info("Disconnected from MQTT broker")
            self._set_state(ConnectionState.DISCONNECTED)

    def _on_message(self, client, userdata, msg):
        """Handle received MQTT message"""
        try:
            self.logger.debug(f"Message received: {msg.topic}")
            self._stats['messages_received'] += 1
            self.message_received.emit(msg.topic, msg.payload)

        except Exception as e:
            self.logger.error(f"Error processing received message: {e}")

    def _on_publish(self, client, userdata, mid):
        """Handle message publish confirmation"""
        with self._message_lock:
            if mid in self._pending_messages:
                message = self._pending_messages.pop(mid)
                self.message_sent.emit(message.topic, message.payload)
                self.logger.debug(f"Message confirmed: {message.topic}")

    def _on_subscribe(self, client, userdata, mid, granted_qos):
        """Handle subscription confirmation"""
        self.logger.debug(f"Subscription confirmed (mid: {mid}, QoS: {granted_qos})")

    def _on_log(self, client, userdata, level, buf):
        """Handle MQTT client logs"""
        if level == mqtt.MQTT_LOG_ERR:
            self.logger.error(f"MQTT: {buf}")
        elif level == mqtt.MQTT_LOG_WARNING:
            self.logger.warning(f"MQTT: {buf}")
        elif level == mqtt.MQTT_LOG_DEBUG:
            self.logger.debug(f"MQTT: {buf}")

    def _schedule_reconnect(self):
        """Schedule reconnection attempt"""
        if self.config.max_reconnect_attempts > 0 and self._reconnect_attempts >= self.config.max_reconnect_attempts:
            self.logger.error("Maximum reconnection attempts reached")
            self._set_state(ConnectionState.ERROR)
            return

        # Calculate delay with exponential backoff
        delay = min(
            self.config.reconnect_delay_max,
            self.config.reconnect_delay_min * (2 ** self._reconnect_attempts)
        )

        self._reconnect_attempts += 1
        self.logger.info(f"Scheduling reconnection attempt {self._reconnect_attempts} in {delay:.1f}s")

        # Use QTimer for reconnection
        QTimer.singleShot(int(delay * 1000), self._attempt_reconnect)

    def _attempt_reconnect(self):
        """Attempt to reconnect"""
        if self._state == ConnectionState.RECONNECTING:
            self.logger.info("Attempting to reconnect...")
            self.connect()