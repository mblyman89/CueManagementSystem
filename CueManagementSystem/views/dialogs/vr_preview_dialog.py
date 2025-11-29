"""
VR Preview Window with Embedded Visualizer
==========================================

Fullscreen window for VR preview with embedded firework visualization.
Displays countdown, then renders fireworks directly in the window.

This eliminates the need for a separate Python visualizer process.
Everything happens in one seamless window.

Features:
- 10-second countdown
- Embedded firework canvas
- Real-time particle rendering
- Auto-start/stop server
- Single-click preview experience

Author: SuperNinja AI
Version: 2.0.0 (Embedded Visualizer)
License: MIT
"""

import math
import random
from datetime import datetime
from typing import List, Tuple
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt, Signal, QTimer, QPointF
from PySide6.QtGui import QKeyEvent, QPainter, QColor, QPen, QBrush


class FireworkParticle:
    """Represents a single particle in a firework explosion"""

    def __init__(self, x, y, vx, vy, color, lifetime=3.0):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.lifetime = lifetime
        self.age = 0.0
        self.size = random.uniform(2, 4)
        self.gravity = 30  # pixels per second squared

    def update(self, dt):
        """Update particle position and age"""
        self.age += dt

        # Update position
        self.x += self.vx * dt
        self.y += self.vy * dt

        # Apply gravity
        self.vy += self.gravity * dt

        # Apply air resistance
        self.vx *= 0.99
        self.vy *= 0.99

        # Check if particle is still alive
        return self.age < self.lifetime

    def get_alpha(self):
        """Get particle alpha based on age"""
        fade_progress = self.age / self.lifetime
        return int(255 * (1.0 - fade_progress))


class Firework:
    """Represents a complete firework effect"""

    def __init__(self, x, y, launch_angle, color, star_count=100):
        self.x = x
        self.y = y
        self.launch_angle = launch_angle
        self.color = color
        self.star_count = star_count
        self.particles = []
        self.exploded = False
        self.launch_time = 0.0
        self.burst_time = 2.5  # Time to burst

        # Launch particle (going up)
        angle_rad = math.radians(90 + launch_angle)  # 90 = straight up
        speed = 200  # pixels per second
        self.launch_vx = speed * math.cos(angle_rad)
        self.launch_vy = -speed * math.sin(angle_rad)  # Negative = up

        self.launch_x = x
        self.launch_y = y

    def update(self, dt):
        """Update firework state"""
        self.launch_time += dt

        if not self.exploded:
            # Update launch position
            self.launch_x += self.launch_vx * dt
            self.launch_y += self.launch_vy * dt
            self.launch_vy += 50 * dt  # Gravity

            # Check if time to explode
            if self.launch_time >= self.burst_time:
                self.explode()
        else:
            # Update particles
            self.particles = [p for p in self.particles if p.update(dt)]

        return len(self.particles) > 0 or not self.exploded

    def explode(self):
        """Create explosion particles"""
        self.exploded = True

        # Create particles in all directions
        for i in range(self.star_count):
            angle = (2 * math.pi * i) / self.star_count
            speed = random.uniform(80, 150)

            vx = speed * math.cos(angle)
            vy = speed * math.sin(angle)

            particle = FireworkParticle(
                self.launch_x, self.launch_y,
                vx, vy,
                self.color,
                lifetime=random.uniform(2.0, 4.0)
            )
            self.particles.append(particle)

    def draw(self, painter):
        """Draw the firework"""
        if not self.exploded:
            # Draw launch trail
            painter.setPen(QPen(QColor(*self.color, 200), 3))
            painter.drawEllipse(QPointF(self.launch_x, self.launch_y), 3, 3)
        else:
            # Draw particles
            for particle in self.particles:
                alpha = particle.get_alpha()
                color = QColor(*self.color, alpha)
                painter.setPen(QPen(color, 2))
                painter.setBrush(QBrush(color))
                painter.drawEllipse(QPointF(particle.x, particle.y), particle.size, particle.size)


class FireworkCanvas(QWidget):
    """Canvas for rendering fireworks"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.fireworks: List[Firework] = []
        self.active_count = 0
        self.last_shell_name = ""
        self.last_time = datetime.now()

        # Set black background
        self.setStyleSheet("background-color: #000000;")

        # Update timer (60 FPS)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_animation)
        self.timer.start(16)  # ~60 FPS

    def add_firework(self, launch_angle: float, color: Tuple[int, int, int], star_count: int = 100,
                     shell_name: str = ""):
        """Add a new firework"""
        # All fireworks launch from center bottom
        x = self.width() / 2
        y = self.height() - 50

        firework = Firework(x, y, launch_angle, color, star_count)
        self.fireworks.append(firework)

        # Update stats
        self.last_shell_name = shell_name
        self.active_count = len([f for f in self.fireworks if not f.exploded or len(f.particles) > 0])

    def update_animation(self):
        """Update animation frame"""
        now = datetime.now()
        dt = (now - self.last_time).total_seconds()
        self.last_time = now

        # Update all fireworks
        self.fireworks = [f for f in self.fireworks if f.update(dt)]

        # Update active count
        self.active_count = len([f for f in self.fireworks if not f.exploded or len(f.particles) > 0])

        # Trigger repaint
        self.update()

    def clear_fireworks(self):
        """Clear all fireworks"""
        self.fireworks.clear()
        self.active_count = 0
        self.last_shell_name = ""

    def paintEvent(self, event):
        """Paint the canvas"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw all fireworks
        for firework in self.fireworks:
            firework.draw(painter)

        # Draw status info in top-right corner
        if self.last_shell_name or self.active_count > 0:
            painter.setPen(QPen(QColor(255, 255, 255, 180)))
            status_text = f"Active: {self.active_count}"
            if self.last_shell_name:
                status_text += f" | Last: {self.last_shell_name}"

            painter.drawText(self.width() - 400, 30, status_text)


class VRPreviewWindow(QWidget):
    """
    Fullscreen window for VR preview with embedded visualizer

    Displays countdown, then renders fireworks directly in the window.
    No separate visualizer process needed!
    """

    # Signals
    preview_cancelled = Signal()  # User pressed Escape

    def __init__(self, parent=None):
        super().__init__(parent)

        # Window setup
        self.setWindowTitle("VR Preview")
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_DeleteOnClose)

        # Make fullscreen
        self.showFullScreen()

        # Setup UI
        self._init_ui()

        # State
        self.is_countdown = True
        self.is_running = False

    def _init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Firework canvas (hidden during countdown)
        self.canvas = FireworkCanvas(self)
        self.canvas.hide()
        layout.addWidget(self.canvas)

        # Countdown overlay (shown during countdown)
        self.countdown_widget = QWidget(self)
        countdown_layout = QVBoxLayout(self.countdown_widget)
        countdown_layout.setContentsMargins(0, 0, 0, 0)

        # Countdown label (centered, large text)
        self.countdown_label = QLabel("10")
        self.countdown_label.setAlignment(Qt.AlignCenter)
        self.countdown_label.setStyleSheet("""
            QLabel {
                color: #FFFFFF;
                font-size: 200px;
                font-weight: bold;
                font-family: Arial, sans-serif;
            }
        """)
        countdown_layout.addWidget(self.countdown_label)

        # Info label (bottom, smaller text)
        self.info_label = QLabel("Press ESC to cancel")
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setStyleSheet("""
            QLabel {
                color: #888888;
                font-size: 20px;
                font-family: Arial, sans-serif;
                padding: 20px;
            }
        """)
        countdown_layout.addWidget(self.info_label, 0, Qt.AlignBottom)

        self.countdown_widget.setStyleSheet("background-color: #000000;")
        layout.addWidget(self.countdown_widget)

        self.setLayout(layout)

    def update_countdown(self, value: int):
        """
        Update countdown display

        Args:
            value: Countdown number (10, 9, 8, ..., 1)
        """
        if value > 0:
            self.countdown_label.setText(str(value))
            self.countdown_label.setStyleSheet("""
                QLabel {
                    color: #FFFFFF;
                    font-size: 200px;
                    font-weight: bold;
                    font-family: Arial, sans-serif;
                }
            """)
        else:
            # Countdown finished, show canvas
            self.show_preview_running()

    def show_preview_running(self):
        """Show preview running - switch to canvas"""
        self.is_countdown = False
        self.is_running = True

        # Hide countdown, show canvas
        self.countdown_widget.hide()
        self.canvas.show()
        self.canvas.clear_fireworks()

    def show_preview_complete(self):
        """Show preview complete message"""
        self.is_running = False

        # Hide canvas, show countdown widget with completion message
        self.canvas.hide()
        self.countdown_widget.show()

        self.countdown_label.setText("PREVIEW COMPLETE")
        self.countdown_label.setStyleSheet("""
            QLabel {
                color: #00FF00;
                font-size: 80px;
                font-weight: bold;
                font-family: Arial, sans-serif;
            }
        """)

        self.info_label.setText("Window will close in 3 seconds...")

    def show_error(self, message: str):
        """
        Show error message

        Args:
            message: Error message to display
        """
        self.is_running = False

        # Hide canvas, show countdown widget with error
        self.canvas.hide()
        self.countdown_widget.show()

        self.countdown_label.setText("ERROR")
        self.countdown_label.setStyleSheet("""
            QLabel {
                color: #FF0000;
                font-size: 80px;
                font-weight: bold;
                font-family: Arial, sans-serif;
            }
        """)

        self.info_label.setText(f"{message}\nPress ESC to close")

    def add_firework(self, launch_angle: float, color: Tuple[int, int, int], star_count: int = 100,
                     shell_name: str = ""):
        """Add a firework to the canvas"""
        if self.is_running:
            self.canvas.add_firework(launch_angle, color, star_count, shell_name)

    def keyPressEvent(self, event: QKeyEvent):
        """Handle key press events"""
        if event.key() == Qt.Key_Escape:
            # User pressed Escape, cancel preview
            self.preview_cancelled.emit()
            self.close()
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event):
        """Handle window close event"""
        # Emit cancellation signal if not already done
        self.preview_cancelled.emit()

        # Stop canvas animation
        if hasattr(self, 'canvas'):
            self.canvas.timer.stop()

        # Ensure we're not fullscreen when closing
        if self.isFullScreen():
            self.showNormal()

        super().closeEvent(event)