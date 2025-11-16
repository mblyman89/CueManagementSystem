"""
Color Manipulation Utilities
============================

Utility functions for lightening and darkening hex color codes using PySide6's QColor.

Features:
- Color lightening function
- Color darkening function
- Hex color code support
- Percentage-based adjustment
- PySide6 QColor integration

Author: Michael Lyman
Version: 1.0.0
License: MIT
"""

from PySide6.QtGui import QColor

def lighten_color(hex_color, percent):
    """Lighten a hex color by given percent (0-100)"""
    color = QColor(hex_color)
    return color.lighter(100 + percent).name()

def darken_color(hex_color, percent):
    """Darken a hex color by given percent (0-100)"""
    color = QColor(hex_color)
    return color.darker(100 + percent).name()