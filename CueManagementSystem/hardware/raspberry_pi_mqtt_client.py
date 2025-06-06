#!/usr/bin/env python3
"""
Raspberry Pi MQTT Client for Cue Management System

This script runs on the Raspberry Pi and receives cue data via MQTT.
It controls shift registers based on the received data.

Usage:
    python3 raspberry_pi_mqtt_client.py [--host HOST] [--port PORT] [--username USERNAME] [--password PASSWORD]

Requirements:
    - paho-mqtt
    - RPi.GPIO
"""

import argparse
import json
import logging
import signal
import sys
import time
from threading import Event

import paho.mqtt.client as mqtt

# Try to import RPi.GPIO, but allow running in simulation mode if not available
try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    print("WARNING: RPi.GPIO not available. Running in simulation mode.")
    GPIO_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/tmp/cue_system.log')
    ]
)
logger = logging.getLogger("CueSystem")

# MQTT Settings
DEFAULT_BROKER_HOST = "localhost"
DEFAULT_BROKER_PORT = 1883
DEFAULT_CLIENT_ID = f"raspberry_pi_client_{int(time.time())}"

# GPIO Pin Definitions for Shift Register
if GPIO_AVAILABLE:
    # Define pins for shift register control
    DATA_PIN = 17    # GPIO pin connected to DS (Serial Data Input)
    LATCH_PIN = 27   # GPIO pin connected to ST_CP (Storage Register Clock Input)
    CLOCK_PIN = 22   # GPIO pin connected to SH_CP (Shift Register Clock Input)
    
    # Additional pins for multiple shift registers (if needed)
    CLEAR_PIN = 23   # GPIO pin connected to MR (Master Reset, active low)
    OE_PIN = 24      # GPIO pin connected to OE (Output Enable, active low)

# MQTT Topics
BASE_TOPIC = "cue_system"
CUE_TOPIC = f"{BASE_TOPIC}/cues"
STATUS_TOPIC = f"{BASE_TOPIC}/status"
COMMAND_TOPIC = f"{BASE_TOPIC}/commands/#"

# Global variables
exit_event = Event()
current_register_states = {}  # Stores the current state of each shift register


class ShiftRegisterController:
    """Controls shift registers connected to the Raspberry Pi"""
    
    def __init__(self):
        """Initialize the shift register controller"""
        self.initialized = False
        
        if not GPIO_AVAILABLE:
            logger.warning("GPIO not available. Shift register operations will be simulated.")
            return
            
        try:
            # Set up GPIO
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(DATA_PIN, GPIO.OUT)
            GPIO.setup(LATCH_PIN, GPIO.OUT)
            GPIO.setup(CLOCK_PIN, GPIO.OUT)
            
            # Set up optional pins if used
            GPIO.setup(CLEAR_PIN, GPIO.OUT)
            GPIO.setup(OE_PIN, GPIO.OUT)
            
            # Initialize pins to default states
            GPIO.output(DATA_PIN, GPIO.LOW)
            GPIO.output(LATCH_PIN, GPIO.LOW)
            GPIO.output(CLOCK_PIN, GPIO.LOW)
            GPIO.output(CLEAR_PIN, GPIO.HIGH)  # Active low, so set HIGH for normal operation
            GPIO.output(OE_PIN, GPIO.LOW)      # Active low, so set LOW to enable outputs
            
            self.initialized = True
            logger.info("Shift register controller initialized")
            
        except Exception as e:
            logger.error(f"Error initializing shift register controller: {e}")
    
    def cleanup(self):
        """Clean up GPIO resources"""
        if GPIO_AVAILABLE and self.initialized:
            GPIO.cleanup()
            logger.info("GPIO resources cleaned up")
    
    def shift_out(self, register_id, value):
        """
        Shift out a byte to the shift register
        
        Args:
            register_id (int): The ID of the register (for multiple registers)
            value (int): The byte value to shift out
        """
        if not GPIO_AVAILABLE or not self.initialized:
            logger.info(f"[SIMULATION] Shifting out value {value} to register {register_id}")
            return
            
        try:
            # Update the current register state
            current_register_states[register_id] = value
            
            # Prepare to send data
            GPIO.output(LATCH_PIN, GPIO.LOW)
            
            # Shift out the data
            for i in range(8):
                bit = (value >> i) & 1
                GPIO.output(DATA_PIN, bit)
                GPIO.output(CLOCK_PIN, GPIO.HIGH)
                time.sleep(0.000001)  # Very short delay
                GPIO.output(CLOCK_PIN, GPIO.LOW)
            
            # Latch the data
            GPIO.output(LATCH_PIN, GPIO.HIGH)
            time.sleep(0.000001)  # Very short delay
            GPIO.output(LATCH_PIN, GPIO.LOW)
            
            logger.debug(f"Shifted out value {value} to register {register_id}")
            
        except Exception as e:
            logger.error(f"Error shifting out data: {e}")
    
    def update_registers(self, registers_data):
        """
        Update all shift registers with new data
        
        Args:
            registers_data (list): List of dictionaries containing register data
        """
        if not registers_data:
            return
            
        for register_data in registers_data:
            register_id = register_data.get("register_id", 0)
            binary_value = register_data.get("binary_value", 0)
            
            # Shift out the data to the appropriate register
            self.shift_out(register_id, binary_value)
            
        logger.info(f"Updated {len(registers_data)} registers")
    
    def clear_all_registers(self):
        """Clear all shift registers (set all outputs to LOW)"""
        if not GPIO_AVAILABLE or not self.initialized:
            logger.info("[SIMULATION] Clearing all registers")
            return
            
        try:
            # Quick clear using the CLEAR pin if available
            GPIO.output(CLEAR_PIN, GPIO.LOW)
            time.sleep(0.000001)  # Very short delay
            GPIO.output(CLEAR_PIN, GPIO.HIGH)
            
            # Also clear our state tracking
            current_register_states.clear()
            
            logger.info("All registers cleared")
            
        except Exception as e:
            logger.error(f"Error clearing registers: {e}")


def on_connect(client, userdata, flags, rc):
    """Callback for when the client connects to the broker"""
    if rc == 0:
        logger.info("Connected to MQTT broker")
        
        # Subscribe to topics
        client.subscribe(CUE_TOPIC)
        client.subscribe(COMMAND_TOPIC)
        
        # Publish online status
        client.publish(STATUS_TOPIC, json.dumps({"status": "online"}), qos=1, retain=True)
    else:
        logger.error(f"Failed to connect to MQTT broker, return code: {rc}")


def on_disconnect(client, userdata, rc):
    """Callback for when the client disconnects from the broker"""
    if rc != 0:
        logger.warning(f"Unexpected disconnection from MQTT broker, return code: {rc}")


def on_message(client, userdata, msg):
    """Callback for when a message is received from the broker"""
    try:
        logger.debug(f"Received message on topic {msg.topic}")
        
        # Parse the JSON payload
        payload = json.loads(msg.payload.decode())
        
        # Process based on topic
        if msg.topic == CUE_TOPIC:
            process_cue(payload)
        elif msg.topic.startswith(f"{BASE_TOPIC}/commands/"):
            process_command(msg.topic, payload)
            
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in message: {msg.payload}")
    except Exception as e:
        logger.error(f"Error processing message: {e}")


def process_cue(cue_data):
    """
    Process a cue message
    
    Args:
        cue_data (dict): The cue data from the MQTT message
    """
    try:
        cue_id = cue_data.get("cue_id", "unknown")
        registers = cue_data.get("registers", [])
        
        logger.info(f"Processing cue {cue_id} with {len(registers)} registers")
        
        # Update the shift registers
        shift_register_controller.update_registers(registers)
        
        # Publish acknowledgment
        client.publish(
            f"{STATUS_TOPIC}/cue_ack",
            json.dumps({
                "cue_id": cue_id,
                "status": "executed",
                "timestamp": time.time()
            }),
            qos=1
        )
        
    except Exception as e:
        logger.error(f"Error processing cue: {e}")


def process_command(topic, command_data):
    """
    Process a command message
    
    Args:
        topic (str): The command topic
        command_data (dict): The command data from the MQTT message
    """
    try:
        command = topic.split('/')[-1]
        logger.info(f"Processing command: {command}")
        
        if command == "clear_all":
            # Clear all shift registers
            shift_register_controller.clear_all_registers()
            
            # Publish acknowledgment
            client.publish(
                f"{STATUS_TOPIC}/command_ack",
                json.dumps({
                    "command": command,
                    "status": "executed",
                    "timestamp": time.time()
                }),
                qos=1
            )
        elif command == "execute":
            # Execute a command (e.g., shell command)
            command_text = command_data.get("command_text", "")
            logger.info(f"Executing command: {command_text}")
            
            # This is a placeholder - you might want to implement actual command execution
            # using subprocess or similar, but be careful about security implications
            
            # Publish acknowledgment
            client.publish(
                f"{STATUS_TOPIC}/command_ack",
                json.dumps({
                    "command": command,
                    "command_text": command_text,
                    "status": "executed",
                    "timestamp": time.time()
                }),
                qos=1
            )
        else:
            logger.warning(f"Unknown command: {command}")
            
    except Exception as e:
        logger.error(f"Error processing command: {e}")


def signal_handler(sig, frame):
    """Handle termination signals"""
    logger.info("Termination signal received. Shutting down...")
    exit_event.set()


def main():
    """Main function"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Raspberry Pi MQTT Client for Cue Management System")
    parser.add_argument("--host", default=DEFAULT_BROKER_HOST, help="MQTT broker host")
    parser.add_argument("--port", type=int, default=DEFAULT_BROKER_PORT, help="MQTT broker port")
    parser.add_argument("--username", help="MQTT username")
    parser.add_argument("--password", help="MQTT password")
    args = parser.parse_args()
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Initialize shift register controller
    global shift_register_controller
    shift_register_controller = ShiftRegisterController()
    
    # Set up MQTT client
    global client
    client = mqtt.Client(client_id=DEFAULT_CLIENT_ID)
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message
    
    # Set username and password if provided
    if args.username and args.password:
        client.username_pw_set(args.username, args.password)
    
    # Set last will message
    client.will_set(STATUS_TOPIC, json.dumps({"status": "offline"}), qos=1, retain=True)
    
    try:
        # Connect to the MQTT broker
        logger.info(f"Connecting to MQTT broker at {args.host}:{args.port}")
        client.connect(args.host, args.port, keepalive=60)
        
        # Start the MQTT loop
        client.loop_start()
        
        # Main loop
        logger.info("Cue System running. Press Ctrl+C to exit.")
        while not exit_event.is_set():
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received. Shutting down...")
    except Exception as e:
        logger.error(f"Error in main loop: {e}")
    finally:
        # Clean up
        logger.info("Cleaning up resources...")
        
        # Publish offline status
        try:
            client.publish(STATUS_TOPIC, json.dumps({"status": "offline"}), qos=1, retain=True)
        except:
            pass
            
        # Stop the MQTT loop
        client.loop_stop()
        
        # Disconnect from the broker
        try:
            client.disconnect()
        except:
            pass
            
        # Clean up GPIO
        shift_register_controller.cleanup()
        
        logger.info("Shutdown complete")


if __name__ == "__main__":
    main()