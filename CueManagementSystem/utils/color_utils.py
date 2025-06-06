from PySide6.QtGui import QColor

def lighten_color(hex_color, percent):
    """Lighten a hex color by given percent (0-100)"""
    color = QColor(hex_color)
    return color.lighter(100 + percent).name()

def darken_color(hex_color, percent):
    """Darken a hex color by given percent (0-100)"""
    color = QColor(hex_color)
    return color.darker(100 + percent).name()