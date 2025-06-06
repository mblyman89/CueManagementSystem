class ShiftRegister:
    """
    Class representing a shift register for controlling outputs on the Raspberry Pi
    
    This class defines the data structure and commands needed to control shift registers
    connected to a Raspberry Pi. It provides methods for setting outputs and generating
    the necessary commands to be sent via MQTT.
    """
    
    def __init__(self, register_id=0, num_outputs=8):
        """
        Initialize a shift register
        
        Args:
            register_id (int): The ID of this shift register (for multiple registers)
            num_outputs (int): The number of outputs on this shift register
        """
        self.register_id = register_id
        self.num_outputs = num_outputs
        self.output_states = [False] * num_outputs
        
    def set_output(self, output_num, state):
        """
        Set the state of a specific output
        
        Args:
            output_num (int): The output number (0-based)
            state (bool): True to turn on, False to turn off
            
        Returns:
            bool: True if successful, False if output_num is invalid
        """
        if 0 <= output_num < self.num_outputs:
            self.output_states[output_num] = bool(state)
            return True
        return False
        
    def set_all_outputs(self, states):
        """
        Set the state of all outputs at once
        
        Args:
            states (list): List of boolean states for each output
            
        Returns:
            bool: True if successful, False if states list is invalid
        """
        if len(states) != self.num_outputs:
            return False
            
        self.output_states = [bool(state) for state in states]
        return True
        
    def clear_all_outputs(self):
        """Turn off all outputs"""
        self.output_states = [False] * self.num_outputs
        
    def get_output_state(self, output_num):
        """
        Get the state of a specific output
        
        Args:
            output_num (int): The output number (0-based)
            
        Returns:
            bool: The state of the output, or None if output_num is invalid
        """
        if 0 <= output_num < self.num_outputs:
            return self.output_states[output_num]
        return None
        
    def get_all_output_states(self):
        """
        Get the state of all outputs
        
        Returns:
            list: List of boolean states for each output
        """
        return self.output_states.copy()
        
    def get_binary_representation(self):
        """
        Get the binary representation of the output states
        
        Returns:
            int: The binary representation of the output states
        """
        binary = 0
        for i, state in enumerate(self.output_states):
            if state:
                binary |= (1 << i)
        return binary
        
    def get_mqtt_payload(self):
        """
        Get the MQTT payload for this shift register
        
        Returns:
            dict: A dictionary containing the register ID and output states
        """
        return {
            "register_id": self.register_id,
            "binary_value": self.get_binary_representation(),
            "output_states": self.output_states
        }


class ShiftRegisterManager:
    """
    Manager for multiple shift registers
    
    This class manages multiple shift registers and provides methods for
    controlling them as a group.
    """
    
    def __init__(self):
        """Initialize the shift register manager"""
        self.registers = {}
        
    def add_register(self, register_id, num_outputs=8):
        """
        Add a shift register to the manager
        
        Args:
            register_id (int): The ID of the register
            num_outputs (int): The number of outputs on the register
            
        Returns:
            ShiftRegister: The newly created shift register
        """
        register = ShiftRegister(register_id, num_outputs)
        self.registers[register_id] = register
        return register
        
    def get_register(self, register_id):
        """
        Get a shift register by ID
        
        Args:
            register_id (int): The ID of the register
            
        Returns:
            ShiftRegister: The shift register, or None if not found
        """
        return self.registers.get(register_id)
        
    def set_output(self, register_id, output_num, state):
        """
        Set the state of a specific output on a specific register
        
        Args:
            register_id (int): The ID of the register
            output_num (int): The output number (0-based)
            state (bool): True to turn on, False to turn off
            
        Returns:
            bool: True if successful, False if register_id or output_num is invalid
        """
        register = self.get_register(register_id)
        if register:
            return register.set_output(output_num, state)
        return False
        
    def clear_all_outputs(self):
        """Turn off all outputs on all registers"""
        for register in self.registers.values():
            register.clear_all_outputs()
            
    def get_mqtt_payload(self):
        """
        Get the MQTT payload for all shift registers
        
        Returns:
            list: A list of dictionaries containing the register IDs and output states
        """
        return [register.get_mqtt_payload() for register in self.registers.values()]
        
    def process_cue(self, cue_data):
        """
        Process a cue and set the appropriate outputs
        
        Args:
            cue_data (dict): The cue data containing output information
            
        Returns:
            dict: The MQTT payload to send to the Raspberry Pi
        """
        # Clear all outputs first
        self.clear_all_outputs()
        
        # Process outputs based on cue type
        cue_type = cue_data.get("cue_type", "")
        output_values = cue_data.get("output_values", [])
        
        # Map output values to registers and outputs
        for output in output_values:
            # Simple mapping: output % 8 gives the output number, output // 8 gives the register ID
            register_id = output // 8
            output_num = output % 8
            
            # Ensure register exists
            if register_id not in self.registers:
                self.add_register(register_id)
                
            # Set the output
            self.set_output(register_id, output_num, True)
            
        # Return the MQTT payload
        return {
            "cue_id": cue_data.get("cue_number", ""),
            "cue_type": cue_type,
            "registers": self.get_mqtt_payload()
        }