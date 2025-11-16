"""
Shift Register Interactive Test
===============================

Interactive testing script for shift register outputs on Raspberry Pi with various firing patterns.

Features:
- Single shot testing
- Double shot testing
- Single run sequences
- Double run sequences
- Configurable delays
- Interactive command-line interface
- GPIO pin control

Author: Michael Lyman
Version: 1.0.0
License: MIT
"""

import RPi.GPIO as GPIO
import time
import sys

# Pin assignments (BCM mode)
PIN_DATA = 7      # SDI (Serial Data Input)
PIN_SCLK = 17     # Serial Clock
PIN_RCLK = 9      # Register Clock (Latch)
PIN_OE = 2        # Output Enable (active LOW)
PIN_SCLR = 13     # Serial Clear (active LOW)

# Timing constants (in seconds)
CLOCK_DELAY = 0.000001  # 1 microsecond
SHOT_DURATION = 1.0     # Duration to keep output HIGH for shots


def setup_gpio():
    """Initialize GPIO pins"""
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    
    # Setup output pins
    GPIO.setup(PIN_DATA, GPIO.OUT)
    GPIO.setup(PIN_SCLK, GPIO.OUT)
    GPIO.setup(PIN_RCLK, GPIO.OUT)
    GPIO.setup(PIN_OE, GPIO.OUT)
    GPIO.setup(PIN_SCLR, GPIO.OUT)
    
    # Initialize pins to safe state
    GPIO.output(PIN_DATA, GPIO.LOW)
    GPIO.output(PIN_SCLK, GPIO.LOW)
    GPIO.output(PIN_RCLK, GPIO.LOW)
    GPIO.output(PIN_OE, GPIO.HIGH)  # Disable outputs (active LOW)
    GPIO.output(PIN_SCLR, GPIO.HIGH)  # Normal operation (active LOW)
    
    print("GPIO initialized successfully")


def clear_shift_register():
    """Clear all shift register outputs using serial clear"""
    GPIO.output(PIN_SCLR, GPIO.LOW)
    time.sleep(0.001)
    GPIO.output(PIN_SCLR, GPIO.HIGH)
    time.sleep(0.001)


def shift_out_bit(bit_value):
    """Shift out a single bit to the shift register"""
    GPIO.output(PIN_DATA, bit_value)
    time.sleep(CLOCK_DELAY)
    GPIO.output(PIN_SCLK, GPIO.HIGH)
    time.sleep(CLOCK_DELAY)
    GPIO.output(PIN_SCLK, GPIO.LOW)
    time.sleep(CLOCK_DELAY)


def latch_data():
    """Latch the shifted data to the output registers"""
    GPIO.output(PIN_RCLK, GPIO.HIGH)
    time.sleep(CLOCK_DELAY)
    GPIO.output(PIN_RCLK, GPIO.LOW)
    time.sleep(CLOCK_DELAY)


def send_data(output_states):
    """
    Send data to shift register
    output_states: list of 0s and 1s, where index 0 is the first output
    """
    # Reverse the list because we shift MSB first
    # but want output 1 to be the first bit shifted
    reversed_states = list(reversed(output_states))
    
    for bit in reversed_states:
        shift_out_bit(bit)
    
    latch_data()


def enable_outputs():
    """Enable shift register outputs"""
    GPIO.output(PIN_OE, GPIO.LOW)  # Active LOW


def disable_outputs():
    """Disable shift register outputs"""
    GPIO.output(PIN_OE, GPIO.HIGH)  # Active LOW


def get_cue_type():
    """Get cue type from user"""
    print("\n" + "="*50)
    print("SHIFT REGISTER TEST SCRIPT")
    print("="*50)
    print("\nSelect cue type:")
    print("1. Single Shot")
    print("2. Double Shot")
    print("3. Single Run")
    print("4. Double Run")
    
    while True:
        choice = input("\nEnter choice (1-4): ").strip()
        if choice in ['1', '2', '3', '4']:
            return int(choice)
        print("Invalid choice. Please enter 1, 2, 3, or 4.")


def get_output_number(prompt="Enter output number (1-64): "):
    """Get a single output number from user"""
    while True:
        try:
            output = int(input(prompt).strip())
            if 1 <= output <= 64:
                return output
            print("Output must be between 1 and 64.")
        except ValueError:
            print("Please enter a valid number.")


def get_output_count(prompt="How many outputs? (1-64): "):
    """Get count of outputs from user"""
    while True:
        try:
            count = int(input(prompt).strip())
            if 1 <= count <= 64:
                return count
            print("Count must be between 1 and 64.")
        except ValueError:
            print("Please enter a valid number.")


def get_delay():
    """Get delay between outputs from user"""
    while True:
        try:
            delay = float(input("Enter delay between outputs (seconds): ").strip())
            if delay >= 0:
                return delay
            print("Delay must be non-negative.")
        except ValueError:
            print("Please enter a valid number.")


def execute_single_shot(output):
    """Execute a single shot on specified output"""
    print(f"\nExecuting SINGLE SHOT on output {output}")
    
    # Create output state array (64 outputs)
    states = [0] * 64
    states[output - 1] = 1  # Set the specified output HIGH
    
    # Clear first
    clear_shift_register()
    
    # Send data and enable outputs
    send_data(states)
    enable_outputs()
    
    print(f"Output {output} is now HIGH")
    time.sleep(SHOT_DURATION)
    
    # Clear and disable
    disable_outputs()
    clear_shift_register()
    
    print(f"Output {output} is now LOW")


def execute_double_shot(output1, output2):
    """Execute a double shot on two specified outputs"""
    print(f"\nExecuting DOUBLE SHOT on outputs {output1} and {output2}")
    
    # Create output state array (64 outputs)
    states = [0] * 64
    states[output1 - 1] = 1  # Set first output HIGH
    states[output2 - 1] = 1  # Set second output HIGH
    
    # Clear first
    clear_shift_register()
    
    # Send data and enable outputs
    send_data(states)
    enable_outputs()
    
    print(f"Outputs {output1} and {output2} are now HIGH")
    time.sleep(SHOT_DURATION)
    
    # Clear and disable
    disable_outputs()
    clear_shift_register()
    
    print(f"Outputs {output1} and {output2} are now LOW")


def execute_single_run(outputs, delay):
    """Execute a single run - outputs turn on and stay on until run finishes"""
    print(f"\nExecuting SINGLE RUN on {len(outputs)} outputs with {delay}s delay")
    print(f"Outputs: {outputs}")
    
    # Track which outputs should be on
    active_outputs = []
    
    for i, output in enumerate(outputs, 1):
        print(f"\n[{i}/{len(outputs)}] Turning on output {output}")
        
        # Add this output to active list
        active_outputs.append(output)
        
        # Create output state array with all active outputs
        states = [0] * 64
        for active_output in active_outputs:
            states[active_output - 1] = 1
        
        # Send data and enable outputs
        send_data(states)
        enable_outputs()
        
        # Wait for delay before next output (except after last one)
        if i < len(outputs):
            time.sleep(delay)
    
    print("\nAll outputs are now ON")
    print("Waiting 1 second before turning off all outputs...")
    time.sleep(1.0)
    
    # Turn off all outputs
    disable_outputs()
    clear_shift_register()
    
    print("All outputs are now OFF")
    print("\nSINGLE RUN complete")


def execute_double_run(output_pairs, delay):
    """Execute a double run - outputs turn on and stay on until run finishes"""
    print(f"\nExecuting DOUBLE RUN on {len(output_pairs)} pairs with {delay}s delay")
    print(f"Output pairs: {output_pairs}")
    
    # Track which outputs should be on
    active_outputs = []
    
    for i, (output1, output2) in enumerate(output_pairs, 1):
        print(f"\n[{i}/{len(output_pairs)}] Turning on outputs {output1} and {output2}")
        
        # Add these outputs to active list
        active_outputs.append(output1)
        active_outputs.append(output2)
        
        # Create output state array with all active outputs
        states = [0] * 64
        for active_output in active_outputs:
            states[active_output - 1] = 1
        
        # Send data and enable outputs
        send_data(states)
        enable_outputs()
        
        # Wait for delay before next pair (except after last one)
        if i < len(output_pairs):
            time.sleep(delay)
    
    print("\nAll outputs are now ON")
    print("Waiting 1 second before turning off all outputs...")
    time.sleep(1.0)
    
    # Turn off all outputs
    disable_outputs()
    clear_shift_register()
    
    print("All outputs are now OFF")
    print("\nDOUBLE RUN complete")


def main():
    """Main program"""
    try:
        # Setup GPIO
        setup_gpio()
        
        # Get cue type
        cue_type = get_cue_type()
        
        if cue_type == 1:  # Single Shot
            output = get_output_number("Which output? (1-64): ")
            execute_single_shot(output)
            
        elif cue_type == 2:  # Double Shot
            output1 = get_output_number("First output? (1-64): ")
            output2 = get_output_number("Second output? (1-64): ")
            execute_double_shot(output1, output2)
            
        elif cue_type == 3:  # Single Run
            count = get_output_count("How many outputs? (1-64): ")
            outputs = []
            print(f"\nEnter {count} output numbers:")
            for i in range(count):
                output = get_output_number(f"Output {i+1}: ")
                outputs.append(output)
            delay = get_delay()
            execute_single_run(outputs, delay)
            
        elif cue_type == 4:  # Double Run
            count = get_output_count("How many output pairs? (1-32): ")
            output_pairs = []
            print(f"\nEnter {count} output pairs:")
            for i in range(count):
                print(f"\nPair {i+1}:")
                output1 = get_output_number("  First output: ")
                output2 = get_output_number("  Second output: ")
                output_pairs.append((output1, output2))
            delay = get_delay()
            execute_double_run(output_pairs, delay)
        
        print("\n" + "="*50)
        print("TEST COMPLETE")
        print("="*50)
        
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\nError: {e}")
    finally:
        # Cleanup
        print("\nCleaning up...")
        disable_outputs()
        clear_shift_register()
        GPIO.cleanup()
        print("GPIO cleanup complete")


if __name__ == "__main__":
    main()