#!/usr/bin/env python3
"""
Execute a complete show with precise timing
"""
import RPi.GPIO as GPIO
import sys
import json
import time
from datetime import datetime

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
    
    data_bits = [0] * OUTPUTS_PER_CHAIN
    data_bits[bit_pos] = 1
    
    shift_out_data(chain, data_bits)
    time.sleep(duration_ms / 1000.0)
    
    data_bits[bit_pos] = 0
    shift_out_data(chain, data_bits)

def execute_cue(cue_data):
    """Execute a single cue"""
    cue_type = cue_data.get('type')
    
    if cue_type == 'SINGLE SHOT':
        output = cue_data.get('output')
        duration = cue_data.get('duration', 500)
        fire_output(output, duration)
        
    elif cue_type == 'DOUBLE SHOT':
        output1 = cue_data.get('output1')
        output2 = cue_data.get('output2')
        duration = cue_data.get('duration', 500)
        
        chain1 = get_chain_for_output(output1)
        chain2 = get_chain_for_output(output2)
        bit_pos1 = get_bit_position_in_chain(output1)
        bit_pos2 = get_bit_position_in_chain(output2)
        
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
        duration = cue_data.get('duration', 500)
        
        for output in range(start_output, end_output + 1):
            fire_output(output, duration)
            if output < end_output:
                time.sleep(delay / 1000.0)
    
    elif cue_type == 'DOUBLE RUN':
        start_output1 = cue_data.get('start_output1')
        end_output1 = cue_data.get('end_output1')
        start_output2 = cue_data.get('start_output2')
        end_output2 = cue_data.get('end_output2')
        delay = cue_data.get('delay', 100)
        duration = cue_data.get('duration', 500)
        
        for i in range(max(end_output1 - start_output1 + 1, end_output2 - start_output2 + 1)):
            output1 = start_output1 + i if start_output1 + i <= end_output1 else None
            output2 = start_output2 + i if start_output2 + i <= end_output2 else None
            
            if output1 and output2:
                chain1 = get_chain_for_output(output1)
                chain2 = get_chain_for_output(output2)
                bit_pos1 = get_bit_position_in_chain(output1)
                bit_pos2 = get_bit_position_in_chain(output2)
                
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
            elif output1:
                fire_output(output1, duration)
            elif output2:
                fire_output(output2, duration)
            
            time.sleep(delay / 1000.0)

def execute_cue_for_show(cue_data, active_outputs):
    """
    Execute a cue during show mode - turns outputs ON but never turns them OFF
    active_outputs is a dict mapping chain_index -> list of 200 bits representing current state
    """
    cue_type = cue_data.get('type')
    
    if cue_type == 'SINGLE SHOT':
        output = cue_data.get('output')
        chain = get_chain_for_output(output)
        bit_pos = get_bit_position_in_chain(output)
        
        # Turn on this output (keep all others in their current state)
        active_outputs[chain][bit_pos] = 1
        shift_out_data(chain, active_outputs[chain])
        
    elif cue_type == 'DOUBLE SHOT':
        output1 = cue_data.get('output1')
        output2 = cue_data.get('output2')
        
        chain1 = get_chain_for_output(output1)
        chain2 = get_chain_for_output(output2)
        bit_pos1 = get_bit_position_in_chain(output1)
        bit_pos2 = get_bit_position_in_chain(output2)
        
        # Turn on both outputs
        active_outputs[chain1][bit_pos1] = 1
        active_outputs[chain2][bit_pos2] = 1
        
        # Shift out data (handle same chain or different chains)
        shift_out_data(chain1, active_outputs[chain1])
        if chain1 != chain2:
            shift_out_data(chain2, active_outputs[chain2])
        
    elif cue_type == 'SINGLE RUN':
        start_output = cue_data.get('start_output')
        end_output = cue_data.get('end_output')
        delay = cue_data.get('delay', 100)
        
        chain = get_chain_for_output(start_output)
        
        # Turn on outputs sequentially with delay
        for output in range(start_output, end_output + 1):
            bit_pos = get_bit_position_in_chain(output)
            active_outputs[chain][bit_pos] = 1
            shift_out_data(chain, active_outputs[chain])
            
            if output < end_output:
                time.sleep(delay / 1000.0)
        
    elif cue_type == 'DOUBLE RUN':
        start_output1 = cue_data.get('start_output1')
        end_output1 = cue_data.get('end_output1')
        start_output2 = cue_data.get('start_output2')
        end_output2 = cue_data.get('end_output2')
        delay = cue_data.get('delay', 100)
        
        chain1 = get_chain_for_output(start_output1)
        chain2 = get_chain_for_output(start_output2)
        
        num_pairs = max(end_output1 - start_output1 + 1, end_output2 - start_output2 + 1)
        
        # Turn on output pairs sequentially with delay
        for i in range(num_pairs):
            output1 = start_output1 + i if start_output1 + i <= end_output1 else None
            output2 = start_output2 + i if start_output2 + i <= end_output2 else None
            
            if output1:
                bit_pos1 = get_bit_position_in_chain(output1)
                active_outputs[chain1][bit_pos1] = 1
            
            if output2:
                bit_pos2 = get_bit_position_in_chain(output2)
                active_outputs[chain2][bit_pos2] = 1
            
            # Shift out data
            shift_out_data(chain1, active_outputs[chain1])
            if chain1 != chain2:
                shift_out_data(chain2, active_outputs[chain2])
            
            if i < num_pairs - 1:
                time.sleep(delay / 1000.0)

def execute_show(show_data):
    """
    Execute a complete show with high-precision timing
    Uses perf_counter for nanosecond precision and hybrid sleep/spin-wait
    Outputs stay ON throughout the show (never turn off)
    """
    cues = show_data.get('cues', [])
    
    if not cues:
        return {"status": "error", "message": "No cues in show"}
    
    # Sort cues by execution time to ensure proper order
    sorted_cues = sorted(cues, key=lambda c: c.get('time', 0))
    
    # Initialize active outputs state for all 5 chains
    # This tracks which outputs are currently on
    active_outputs = {
        0: [0] * OUTPUTS_PER_CHAIN,
        1: [0] * OUTPUTS_PER_CHAIN,
        2: [0] * OUTPUTS_PER_CHAIN,
        3: [0] * OUTPUTS_PER_CHAIN,
        4: [0] * OUTPUTS_PER_CHAIN
    }
    
    # Use perf_counter for high-precision timing (nanosecond resolution)
    start_time = time.perf_counter()
    
    # Track timing statistics
    timing_errors = []
    
    for cue in sorted_cues:
        # Target time in seconds
        target_time = cue.get('time', 0) / 1000.0
        
        # Wait with high precision
        current_time = time.perf_counter() - start_time
        wait_time = target_time - current_time
        
        if wait_time > 0:
            # Hybrid sleep/spin-wait for precision
            if wait_time > 0.001:  # If more than 1ms to wait
                # Sleep for most of the time (minus 500μs buffer)
                sleep_time = wait_time - 0.0005
                if sleep_time > 0:
                    time.sleep(sleep_time)
            
            # Spin-wait for final microseconds (high precision)
            while (time.perf_counter() - start_time) < target_time:
                pass  # Busy-wait for precise timing
        
        # Record actual execution time
        actual_time = time.perf_counter() - start_time
        timing_error = (actual_time - target_time) * 1000  # Error in milliseconds
        timing_errors.append(timing_error)
        
        # Execute the cue for show (outputs stay on)
        execute_cue_for_show(cue, active_outputs)
    
    # Calculate timing statistics
    total_duration = time.perf_counter() - start_time
    avg_error = sum(timing_errors) / len(timing_errors) if timing_errors else 0
    max_error = max(timing_errors) if timing_errors else 0
    
    return {
        "status": "success",
        "message": f"Show executed: {len(cues)} cues",
        "duration": total_duration,
        "timing_stats": {
            "average_error_ms": round(avg_error, 4),
            "max_error_ms": round(max_error, 4),
            "total_cues": len(cues)
        }
    }

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"status": "error", "message": "Usage: execute_show.py '<show_file_path>' [start_timestamp]"}))
        sys.exit(1)
    
    try:
        arg = sys.argv[1]
        start_timestamp = float(sys.argv[2]) if len(sys.argv) > 2 else None
        
        # Check if argument is a file path or JSON string
        if arg.startswith('{'):
            # Direct JSON string
            show_data = json.loads(arg)
        else:
            # File path - read JSON from file
            import os
            file_path = os.path.expanduser(arg)
            with open(file_path, 'r') as f:
                show_data = json.load(f)
        
        # If start timestamp provided, wait until that exact time
        if start_timestamp:
            print(f"[Sync] Waiting for start timestamp: {start_timestamp}", file=sys.stderr)
            print(f"[Sync] Current time: {time.time()}", file=sys.stderr)
            print(f"[Sync] Wait duration: {(start_timestamp - time.time()) * 1000:.1f}ms", file=sys.stderr)
            
            # Sleep until close to start time (leave 1ms buffer)
            while time.time() < start_timestamp - 0.001:
                time.sleep(0.001)  # Sleep 1ms at a time
            
            # Spin-wait for final precision
            while time.time() < start_timestamp:
                pass  # Busy-wait for exact moment
            
            actual_start = time.time()
            sync_error = (actual_start - start_timestamp) * 1000  # Error in milliseconds
            print(f"[Sync] Show started at: {actual_start}", file=sys.stderr)
            print(f"[Sync] Sync error: {sync_error:.3f}ms", file=sys.stderr)
        
        setup_gpio()
        result = execute_show(show_data)
        print(json.dumps(result))
        sys.exit(0)
        
    except Exception as e:
        print(json.dumps({"status": "error", "message": str(e)}))
        sys.exit(1)

if __name__ == "__main__":
    main()