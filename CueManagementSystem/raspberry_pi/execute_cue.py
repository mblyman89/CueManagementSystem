#!/usr/bin/env python3
"""
Execute a single cue on the shift registers
"""
import RPi.GPIO as GPIO
import sys
import json
import time

# GPIO Pin Definitions (BCM numbering)
OUTPUT_ENABLE_PINS = [2, 3, 4, 5, 6]
SERIAL_CLEAR_PINS = [13, 16, 19, 20, 26]
DATA_PINS = [7, 8, 12, 14, 15]
SCLK_PINS = [17, 18, 22, 23, 27]
RCLK_PINS = [9, 10, 11, 24, 25]
ARM_PIN = 21

# Constants
OUTPUTS_PER_CHAIN = 200
REGISTERS_PER_CHAIN = 25
BITS_PER_REGISTER = 8

def setup_gpio():
    """Initialize GPIO pins"""
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    
    for pin in OUTPUT_ENABLE_PINS + SERIAL_CLEAR_PINS + DATA_PINS + SCLK_PINS + RCLK_PINS + [ARM_PIN]:
        GPIO.setup(pin, GPIO.OUT)

def get_chain_for_output(output_num):
    """Determine which chain an output belongs to (0-4)"""
    return (output_num - 1) // OUTPUTS_PER_CHAIN

def get_bit_position_in_chain(output_num):
    """Get the bit position within a chain (0-199)"""
    return (output_num - 1) % OUTPUTS_PER_CHAIN

def shift_out_data(chain, data_bits):
    """
    Shift out 200 bits of data to a specific chain
    Optimized for speed - GPIO operations provide sufficient delay
    """
    data_pin = DATA_PINS[chain]
    clock_pin = SCLK_PINS[chain]
    latch_pin = RCLK_PINS[chain]
    
    # Shift out data (MSB first)
    # No sleep needed - GPIO operations are slow enough for 74HC595
    for bit in reversed(data_bits):
        GPIO.output(data_pin, bit)
        GPIO.output(clock_pin, GPIO.HIGH)
        GPIO.output(clock_pin, GPIO.LOW)
    
    # Latch the data
    GPIO.output(latch_pin, GPIO.HIGH)
    GPIO.output(latch_pin, GPIO.LOW)

def fire_output(output_num, duration_ms):
    """Fire a single output for specified duration"""
    chain = get_chain_for_output(output_num)
    bit_pos = get_bit_position_in_chain(output_num)
    
    # Create data array (200 bits, all 0 except the target bit)
    data_bits = [0] * OUTPUTS_PER_CHAIN
    data_bits[bit_pos] = 1
    
    # Shift out data to turn on the output
    shift_out_data(chain, data_bits)
    
    # Wait for duration
    time.sleep(duration_ms / 1000.0)
    
    # Clear the output
    data_bits[bit_pos] = 0
    shift_out_data(chain, data_bits)

def execute_cue(cue_data):
    """Execute a cue based on its type"""
    cue_type = cue_data.get('type')
    
    if cue_type == 'SINGLE SHOT':
        output = cue_data.get('output')
        duration = cue_data.get('duration', 1000)  # Changed to 1 second default
        fire_output(output, duration)
        
    elif cue_type == 'DOUBLE SHOT':
        output1 = cue_data.get('output1')
        output2 = cue_data.get('output2')
        duration = cue_data.get('duration', 1000)  # Changed to 1 second default
        
        # Fire both outputs simultaneously
        chain1 = get_chain_for_output(output1)
        chain2 = get_chain_for_output(output2)
        bit_pos1 = get_bit_position_in_chain(output1)
        bit_pos2 = get_bit_position_in_chain(output2)
        
        # If same chain, combine bits
        if chain1 == chain2:
            data_bits = [0] * OUTPUTS_PER_CHAIN
            data_bits[bit_pos1] = 1
            data_bits[bit_pos2] = 1
            shift_out_data(chain1, data_bits)
            time.sleep(duration / 1000.0)
            data_bits[bit_pos1] = 0
            data_bits[bit_pos2] = 0
            shift_out_data(chain1, data_bits)
        else:
            # Different chains - fire separately but quickly
            data_bits1 = [0] * OUTPUTS_PER_CHAIN
            data_bits1[bit_pos1] = 1
            data_bits2 = [0] * OUTPUTS_PER_CHAIN
            data_bits2[bit_pos2] = 1
            
            shift_out_data(chain1, data_bits1)
            shift_out_data(chain2, data_bits2)
            time.sleep(duration / 1000.0)
            
            data_bits1[bit_pos1] = 0
            data_bits2[bit_pos2] = 0
            shift_out_data(chain1, data_bits1)
            shift_out_data(chain2, data_bits2)
    
    elif cue_type == 'SINGLE RUN':
        start_output = cue_data.get('start_output')
        end_output = cue_data.get('end_output')
        delay = cue_data.get('delay', 100)
        
        # Get chain and create data array
        chain = get_chain_for_output(start_output)
        data_bits = [0] * OUTPUTS_PER_CHAIN
        
        # Turn on outputs sequentially, keeping previous ones on
        for output in range(start_output, end_output + 1):
            bit_pos = get_bit_position_in_chain(output)
            data_bits[bit_pos] = 1
            shift_out_data(chain, data_bits)
            
            if output < end_output:
                time.sleep(delay / 1000.0)
        
        # Hold all outputs on for 1 second
        time.sleep(1.0)
        
        # Turn off all outputs in the run
        for output in range(start_output, end_output + 1):
            bit_pos = get_bit_position_in_chain(output)
            data_bits[bit_pos] = 0
        shift_out_data(chain, data_bits)
    
    elif cue_type == 'DOUBLE RUN':
        start_output1 = cue_data.get('start_output1')
        end_output1 = cue_data.get('end_output1')
        start_output2 = cue_data.get('start_output2')
        end_output2 = cue_data.get('end_output2')
        delay = cue_data.get('delay', 100)
        
        # Get chains for both runs
        chain1 = get_chain_for_output(start_output1)
        chain2 = get_chain_for_output(start_output2)
        
        # Create data arrays for each chain
        data_bits1 = [0] * OUTPUTS_PER_CHAIN
        data_bits2 = [0] * OUTPUTS_PER_CHAIN
        
        # Turn on output pairs sequentially, keeping previous ones on
        num_pairs = max(end_output1 - start_output1 + 1, end_output2 - start_output2 + 1)
        
        for i in range(num_pairs):
            output1 = start_output1 + i if start_output1 + i <= end_output1 else None
            output2 = start_output2 + i if start_output2 + i <= end_output2 else None
            
            if output1:
                bit_pos1 = get_bit_position_in_chain(output1)
                data_bits1[bit_pos1] = 1
            
            if output2:
                bit_pos2 = get_bit_position_in_chain(output2)
                data_bits2[bit_pos2] = 1
            
            # Shift out data to both chains
            if chain1 == chain2:
                # Same chain - combine the data
                combined_bits = [data_bits1[j] | data_bits2[j] for j in range(OUTPUTS_PER_CHAIN)]
                shift_out_data(chain1, combined_bits)
            else:
                # Different chains
                shift_out_data(chain1, data_bits1)
                shift_out_data(chain2, data_bits2)
            
            if i < num_pairs - 1:
                time.sleep(delay / 1000.0)
        
        # Hold all outputs on for 1 second
        time.sleep(1.0)
        
        # Turn off all outputs in both runs
        for i in range(num_pairs):
            output1 = start_output1 + i if start_output1 + i <= end_output1 else None
            output2 = start_output2 + i if start_output2 + i <= end_output2 else None
            
            if output1:
                bit_pos1 = get_bit_position_in_chain(output1)
                data_bits1[bit_pos1] = 0
            
            if output2:
                bit_pos2 = get_bit_position_in_chain(output2)
                data_bits2[bit_pos2] = 0
        
        # Shift out cleared data
        if chain1 == chain2:
            combined_bits = [data_bits1[j] | data_bits2[j] for j in range(OUTPUTS_PER_CHAIN)]
            shift_out_data(chain1, combined_bits)
        else:
            shift_out_data(chain1, data_bits1)
            shift_out_data(chain2, data_bits2)
    
    return {"status": "success", "message": f"Cue executed: {cue_type}"}

def main():
    if len(sys.argv) != 2:
        print(json.dumps({"status": "error", "message": "Usage: execute_cue.py '<cue_json>'"}))
        sys.exit(1)
    
    try:
        cue_data = json.loads(sys.argv[1])
        setup_gpio()
        result = execute_cue(cue_data)
        print(json.dumps(result))
        sys.exit(0)
        
    except Exception as e:
        print(json.dumps({"status": "error", "message": str(e)}))
        sys.exit(1)

if __name__ == "__main__":
    main()