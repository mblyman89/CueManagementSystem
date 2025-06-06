import paho.mqtt.client as mqtt
import json
import asyncio
import threading
import time
import logging
from queue import Queue

class MQTTClient:
    """
    MQTT Client for communicating with Raspberry Pi
    
    This class provides a robust, non-blocking way to send cue data to a Raspberry Pi
    using the MQTT protocol. It handles connection management, message publishing,
    and reconnection attempts automatically.
    """
    
    def __init__(self):
        """Initialize the MQTT client"""
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_message = self.on_message
        self.client.on_publish = self.on_publish
        
        # Default connection settings
        self.broker_host = "raspberrypi.local"
        self.broker_port = 1883
        self.username = None
        self.password = None
        self.client_id = f"cue_system_{int(time.time())}"
        
        # Topics
        self.base_topic = "cue_system"
        self.cue_topic = f"{self.base_topic}/cues"
        self.status_topic = f"{self.base_topic}/status"
        self.command_topic = f"{self.base_topic}/commands"
        
        # Connection state
        self.connected = False
        self.connecting = False
        self.should_reconnect = False
        self.reconnect_delay = 1  # Start with 1 second delay
        self.max_reconnect_delay = 60  # Maximum delay of 60 seconds
        
        # Message queue for outgoing messages
        self.message_queue = Queue()
        
        # Background thread for MQTT loop
        self.mqtt_thread = None
        self.running = False
        
        # Callbacks
        self.on_connection_changed_callback = None
        self.on_message_received_callback = None
        
    def set_connection_params(self, host, port=1883, username=None, password=None):
        """Set connection parameters for the MQTT broker"""
        self.broker_host = host
        self.broker_port = port
        self.username = username
        self.password = password
        
        # Update client with new credentials if provided
        if username and password:
            self.client.username_pw_set(username, password)
            
    def start(self):
        """Start the MQTT client in a background thread"""
        if self.mqtt_thread and self.mqtt_thread.is_alive():
            return  # Already running
            
        self.running = True
        self.should_reconnect = True
        self.mqtt_thread = threading.Thread(target=self._mqtt_loop, daemon=True)
        self.mqtt_thread.start()
        
    def stop(self):
        """Stop the MQTT client"""
        self.running = False
        self.should_reconnect = False
        
        if self.connected:
            try:
                # Publish a last will message
                self.client.publish(self.status_topic, json.dumps({"status": "offline"}), qos=1, retain=True)
                self.client.disconnect()
            except Exception as e:
                logging.error(f"Error disconnecting MQTT client: {e}")
                
        # Wait for thread to finish
        if self.mqtt_thread and self.mqtt_thread.is_alive():
            self.mqtt_thread.join(timeout=2.0)
            
    def _mqtt_loop(self):
        """Main MQTT loop running in background thread"""
        while self.running:
            # Try to connect if not connected
            if not self.connected and not self.connecting and self.should_reconnect:
                self._connect()
                
            # Process message queue if connected
            if self.connected:
                while not self.message_queue.empty():
                    topic, payload, qos, retain = self.message_queue.get()
                    try:
                        self.client.publish(topic, payload, qos, retain)
                    except Exception as e:
                        logging.error(f"Error publishing message: {e}")
                        # Put message back in queue
                        self.message_queue.put((topic, payload, qos, retain))
                        break
            
            # Small sleep to prevent CPU hogging
            time.sleep(0.01)
            
    def _connect(self):
        """Attempt to connect to the MQTT broker"""
        if self.connecting:
            return
            
        self.connecting = True
        try:
            # Set last will message
            self.client.will_set(self.status_topic, json.dumps({"status": "offline"}), qos=1, retain=True)
            
            # Connect to broker
            self.client.connect_async(self.broker_host, self.broker_port, keepalive=60)
            
            # Start the loop
            self.client.loop_start()
            
        except Exception as e:
            logging.error(f"Error connecting to MQTT broker: {e}")
            self.connecting = False
            self._schedule_reconnect()
            
    def _schedule_reconnect(self):
        """Schedule a reconnection attempt with exponential backoff"""
        if not self.should_reconnect:
            return
            
        # Use exponential backoff for reconnection attempts
        time.sleep(self.reconnect_delay)
        self.reconnect_delay = min(self.reconnect_delay * 2, self.max_reconnect_delay)
        
    def on_connect(self, client, userdata, flags, rc):
        """Callback for when the client connects to the broker"""
        self.connecting = False
        
        if rc == 0:
            self.connected = True
            self.reconnect_delay = 1  # Reset reconnect delay
            
            # Subscribe to topics
            self.client.subscribe(f"{self.status_topic}/+")
            self.client.subscribe(f"{self.command_topic}/+")
            
            # Publish online status
            self.client.publish(self.status_topic, json.dumps({"status": "online"}), qos=1, retain=True)
            
            logging.info(f"Connected to MQTT broker at {self.broker_host}:{self.broker_port}")
            
            # Call connection callback if set
            if self.on_connection_changed_callback:
                self.on_connection_changed_callback(True)
        else:
            self.connected = False
            logging.error(f"Failed to connect to MQTT broker, return code: {rc}")
            
            # Call connection callback if set
            if self.on_connection_changed_callback:
                self.on_connection_changed_callback(False)
                
            # Schedule reconnect
            self._schedule_reconnect()
            
    def on_disconnect(self, client, userdata, rc):
        """Callback for when the client disconnects from the broker"""
        self.connected = False
        self.connecting = False
        
        if rc != 0:
            logging.warning(f"Unexpected disconnection from MQTT broker, return code: {rc}")
            
        # Call connection callback if set
        if self.on_connection_changed_callback:
            self.on_connection_changed_callback(False)
            
        # Schedule reconnect if needed
        if self.should_reconnect:
            self._schedule_reconnect()
            
    def on_message(self, client, userdata, msg):
        """Callback for when a message is received from the broker"""
        try:
            payload = json.loads(msg.payload.decode())
            logging.debug(f"Received message on topic {msg.topic}: {payload}")
            
            # Call message callback if set
            if self.on_message_received_callback:
                self.on_message_received_callback(msg.topic, payload)
                
        except Exception as e:
            logging.error(f"Error processing received message: {e}")
            
    def on_publish(self, client, userdata, mid):
        """Callback for when a message is published to the broker"""
        logging.debug(f"Message {mid} published successfully")
        
    def publish_cue(self, cue_data, qos=1):
        """
        Publish cue data to the MQTT broker
        
        Args:
            cue_data (dict): The cue data to publish
            qos (int): Quality of Service level (0, 1, or 2)
        
        Returns:
            bool: True if the message was queued successfully, False otherwise
        """
        try:
            # Convert cue data to JSON
            payload = json.dumps(cue_data)
            
            # Add to message queue
            self.message_queue.put((self.cue_topic, payload, qos, False))
            
            return True
        except Exception as e:
            logging.error(f"Error publishing cue: {e}")
            return False
            
    def publish_command(self, command, data=None, qos=1):
        """
        Publish a command to the MQTT broker
        
        Args:
            command (str): The command to publish
            data (dict): Additional data for the command
            qos (int): Quality of Service level (0, 1, or 2)
            
        Returns:
            bool: True if the message was queued successfully, False otherwise
        """
        try:
            # Prepare command data
            command_data = {
                "command": command,
                "timestamp": time.time()
            }
            
            # Add additional data if provided
            if data:
                command_data["data"] = data
                
            # Convert to JSON
            payload = json.dumps(command_data)
            
            # Add to message queue
            topic = f"{self.command_topic}/{command}"
            self.message_queue.put((topic, payload, qos, False))
            
            return True
        except Exception as e:
            logging.error(f"Error publishing command: {e}")
            return False
            
    def set_on_connection_changed(self, callback):
        """Set callback for connection state changes"""
        self.on_connection_changed_callback = callback
        
    def set_on_message_received(self, callback):
        """Set callback for received messages"""
        self.on_message_received_callback = callback
        
    def is_connected(self):
        """Check if client is connected to the broker"""
        return self.connected