"""Mock RPi.GPIO for off-hardware testing of execute_show.py logic."""
BCM = "BCM"
OUT = "OUT"
HIGH = 1
LOW = 0

def setmode(mode):
    pass

def setwarnings(flag):
    pass

def setup(pin, mode):
    pass

def output(pin, value):
    pass

def cleanup():
    pass
