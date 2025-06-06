import asyncio
import logging
from hardware.mqtt_client import MQTTClient
from hardware.shift_register import ShiftRegisterManager

class HardwareController:
    """
    Controller for managing hardware interactions with the Raspberry Pi
    
    This class integrates the MQTT client and shift register manager to provide
    a high-level interface for sending cue data to the Raspberry Pi.
    """
    
    def __init__(self, system_mode=None):
        """
        Initialize the hardware controller
        
        Args:
            system_mode: Reference to the SystemMode controller
        """
        self.system_mode = system_mode
        self.mqtt_client = MQTTClient()
        self.shift_register_manager = ShiftRegisterManager()
        
        # Set up default registers (can be configured later)
        self.shift_register_manager.add_register(0)  # First register (outputs 0-7)
        self.shift_register_manager.add_register(1)  # Second register (outputs 8-15)
        
        # Connection state
        self.is_connected = False
        
        # Set up MQTT callbacks
        self.mqtt_client.set_on_connection_changed(self._handle_connection_changed)
        self.mqtt_client.set_on_message_received(self._handle_message_received)
        
        # Callback for connection state changes
        self.on_connection_changed_callback = None
        
    def set_connection_params(self, host, port=1883, username=None, password=None):
        """
        Set connection parameters for the MQTT broker
        
        Args:
            host (str): The hostname or IP address of the MQTT broker
            port (int): The port number of the MQTT broker
            username (str): The username for authentication (optional)
            password (str): The password for authentication (optional)
        """
        self.mqtt_client.set_connection_params(host, port, username, password)
        
    def connect(self):
        """
        Connect to the MQTT broker
        
        Returns:
            bool: True if connection attempt was initiated
        """
        try:
            # Start the MQTT client
            self.mqtt_client.start()
            return True
        except Exception as e:
            logging.error(f"Error connecting to MQTT broker: {e}")
            return False
            
    def disconnect(self):
        """
        Disconnect from the MQTT broker
        
        Returns:
            bool: True if disconnection was successful
        """
        try:
            # Stop the MQTT client
            self.mqtt_client.stop()
            return True
        except Exception as e:
            logging.error(f"Error disconnecting from MQTT broker: {e}")
            return False
            
    def is_hardware_connected(self):
        """
        Check if connected to the hardware
        
        Returns:
            bool: True if connected to the MQTT broker
        """
        return self.is_connected
        
    async def send_cue(self, cue_data):
        """
        Send a cue to the Raspberry Pi
        
        Args:
            cue_data (dict): The cue data to send
            
        Returns:
            tuple: (success, message)
        """
        try:
            # Check if we're connected
            if not self.is_connected:
                return False, "Not connected to hardware"
                
            # Process the cue data with the shift register manager
            mqtt_payload = self.shift_register_manager.process_cue(cue_data)
            
            # Publish the cue data
            success = self.mqtt_client.publish_cue(mqtt_payload)
            
            if success:
                return True, f"Cue {cue_data.get('cue_number', '')} sent successfully"
            else:
                return False, "Failed to send cue"
                
        except Exception as e:
            logging.error(f"Error sending cue: {e}")
            return False, f"Error sending cue: {str(e)}"
            
    async def send_command(self, command, data=None):
        """
        Send a command to the Raspberry Pi
        
        Args:
            command (str): The command to send
            data (dict): Additional data for the command
            
        Returns:
            tuple: (success, message)
        """
        try:
            # Check if we're connected
            if not self.is_connected:
                return False, "Not connected to hardware"
                
            # Publish the command
            success = self.mqtt_client.publish_command(command, data)
            
            if success:
                return True, f"Command '{command}' sent successfully"
            else:
                return False, "Failed to send command"
                
        except Exception as e:
            logging.error(f"Error sending command: {e}")
            return False, f"Error sending command: {str(e)}"
            
    async def clear_all_outputs(self):
        """
        Clear all outputs on all shift registers
        
        Returns:
            tuple: (success, message)
        """
        try:
            # Clear all outputs in the shift register manager
            self.shift_register_manager.clear_all_outputs()
            
            # Send the updated state
            mqtt_payload = {
                "command": "clear_all",
                "registers": self.shift_register_manager.get_mqtt_payload()
            }
            
            # Publish the command
            success = self.mqtt_client.publish_command("clear_all", mqtt_payload)
            
            if success:
                return True, "All outputs cleared successfully"
            else:
                return False, "Failed to clear outputs"
                
        except Exception as e:
            logging.error(f"Error clearing outputs: {e}")
            return False, f"Error clearing outputs: {str(e)}"
            
    def set_on_connection_changed(self, callback):
        """
        Set callback for connection state changes
        
        Args:
            callback: Function to call when connection state changes
        """
        self.on_connection_changed_callback = callback
        
    def _handle_connection_changed(self, connected):
        """
        Handle connection state changes from MQTT client
        
        Args:
            connected (bool): True if connected, False if disconnected
        """
        self.is_connected = connected
        
        # Call the callback if set
        if self.on_connection_changed_callback:
            self.on_connection_changed_callback(connected)
            
    def _handle_message_received(self, topic, payload):
        """
        Handle messages received from the MQTT broker
        
        Args:
            topic (str): The topic the message was received on
            payload (dict): The message payload
        """
        # Log the message
        logging.debug(f"Received message on topic {topic}: {payload}")
        
        # Process the message based on the topic
        if topic.startswith(f"{self.mqtt_client.status_topic}/"):
            # Status message
            self._handle_status_message(topic, payload)
        elif topic.startswith(f"{self.mqtt_client.command_topic}/"):
            # Command response
            self._handle_command_response(topic, payload)
            
    def _handle_status_message(self, topic, payload):
        """
        Handle status messages from the Raspberry Pi
        
        Args:
            topic (str): The topic the message was received on
            payload (dict): The message payload
        """
        # Example implementation - can be expanded based on needs
        status = payload.get("status")
        if status == "online":
            logging.info("Raspberry Pi is online")
        elif status == "offline":
            logging.warning("Raspberry Pi is offline")
            
    def _handle_command_response(self, topic, payload):
        """
        Handle command responses from the Raspberry Pi
        
        Args:
            topic (str): The topic the message was received on
            payload (dict): The message payload
        """
        # Example implementation - can be expanded based on needs
        command = payload.get("command")
        success = payload.get("success", False)
        
        if success:
            logging.info(f"Command '{command}' executed successfully on Raspberry Pi")
        else:
            error = payload.get("error", "Unknown error")
            logging.error(f"Command '{command}' failed on Raspberry Pi: {error}")
