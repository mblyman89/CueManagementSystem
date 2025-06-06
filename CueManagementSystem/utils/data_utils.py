def get_sample_cues():
    """
    Returns a list of sample cue data for testing purposes.
    Each cue contains: [cue_number, type, outputs, delay, execute_time]
    Note: # OF OUTPUTS and DURATION are now calculated
    """
    return [
        [1, "SINGLE SHOT", "1", 0.00, "0:00.00"],
        [2, "DOUBLE SHOT", "2,3", 0.00, "1:00.25"],
        [3, "SINGLE RUN", "4,5,6,7,8,9", 0.50, "2:00.50"],
        [4, "DOUBLE RUN", "10,11,12,13,14,15", 0.25, "5:00.75"],
        [5, "SINGLE SHOT", "16", 0.00, "6:00.00"],
        [6, "SINGLE RUN", "17,18,19", 0.30, "7:00.30"],
        [7, "DOUBLE RUN", "20,21,22,23", 0.40, "8:00.40"],
        [8, "DOUBLE SHOT", "24,25", 0.00, "9:00.00"]
    ]

def get_test_data():
    """
    Returns all test data sets
    """
    return {
        'cues': get_sample_cues(),
        'led_panel': get_sample_cues()  # Using same data for consistency
    }