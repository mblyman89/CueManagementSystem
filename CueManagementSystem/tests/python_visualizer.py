"""
Python Firework Visualizer - Quick Testing Client
==================================================

Simple Python-based visualizer for testing the VR preview system.
Connects to the WebSocket server and displays fireworks using PyQt6.

This is a quick prototype for testing the VR preview flow, T=0 synchronization,
and cue execution timing before building the full UE5 visualization.

Features:
- WebSocket client connection
- Simple particle-based firework effects
- Launch angle visualization
- Color support
- Real-time display

Usage:
    python python_visualizer.py

Author: SuperNinja AI
Version: 1.0.0
"""

import sys
import asyncio
import json
import websockets
from datetime import datetime
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QLabel, QVBoxLayout
from PySide6.QtCore import Qt, QTimer, Signal, QObject, QPointF, QThread
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QFont
import math
import random
import threading


class FireworkParticle:
    """Represents a single firework particle"""

    def __init__(self, x, y, vx, vy, color, lifetime=3.0):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.lifetime = lifetime
        self.age = 0.0
        self.size = 3
        self.gravity = 50  # pixels per second squared

    def update(self, dt):
        """Update particle position"""
        self.age += dt

        # Apply velocity
        self.x += self.vx * dt
        self.y += self.vy * dt

        # Apply gravity
        self.vy += self.gravity * dt

        # Fade out
        alpha = max(0, 1.0 - (self.age / self.lifetime))
        return alpha > 0.01  # Return True if still alive

    def get_alpha(self):
        """Get current alpha based on age"""
        return max(0, int(255 * (1.0 - (self.age / self.lifetime))))


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


class VisualizerCanvas(QWidget):
    """Canvas for drawing fireworks"""

    def __init__(self):
        super().__init__()
        self.fireworks = []
        self.setMinimumSize(1200, 800)
        self.setStyleSheet("background-color: #000000;")

        # Update timer (60 FPS)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_animation)
        self.timer.start(16)  # ~60 FPS

        self.last_time = datetime.now()

    def add_firework(self, launch_angle, color, star_count=100):
        """Add a new firework"""
        # All fireworks launch from the same central position
        # The launch angle determines where they explode
        x = self.width() / 2  # Center of screen
        y = self.height() - 50  # Bottom of screen

        firework = Firework(x, y, launch_angle, color, star_count)
        self.fireworks.append(firework)

    def update_animation(self):
        """Update animation frame"""
        now = datetime.now()
        dt = (now - self.last_time).total_seconds()
        self.last_time = now

        # Update all fireworks
        self.fireworks = [fw for fw in self.fireworks if fw.update(dt)]

        # Trigger repaint
        self.update()

    def paintEvent(self, event):
        """Paint the canvas"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw all fireworks
        for firework in self.fireworks:
            firework.draw(painter)

        # Draw info text
        painter.setPen(QPen(QColor(255, 255, 255, 150)))
        painter.setFont(QFont("Arial", 12))
        painter.drawText(10, 20, f"Active Fireworks: {len(self.fireworks)}")
        painter.drawText(10, 40, "Connected to: ws://localhost:8765")


class WebSocketClient(QObject):
    """WebSocket client for receiving firework data"""

    firework_received = Signal(dict)
    connection_status = Signal(str)

    def __init__(self):
        super().__init__()
        self.websocket = None
        self.running = False
        self.loop = None
        self.thread = None

    def start_connection(self, uri="ws://localhost:8765"):
        """Start connection in separate thread"""
        self.thread = threading.Thread(target=self._run_async_loop, args=(uri,), daemon=True)
        self.thread.start()

    def _run_async_loop(self, uri):
        """Run async event loop in thread"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self.connect(uri))

    async def connect(self, uri="ws://localhost:8765"):
        """Connect to WebSocket server with retry"""
        retry_count = 0
        max_retries = 999999  # Retry indefinitely
        retry_delay = 2  # seconds

        while retry_count < max_retries:
            try:
                if retry_count > 0:
                    self.connection_status.emit(f"Connecting... (attempt {retry_count + 1})")
                else:
                    self.connection_status.emit("Connecting...")

                self.websocket = await websockets.connect(uri)
                self.running = True
                self.connection_status.emit("Connected")

                # Send connected message
                await self.websocket.send(json.dumps({
                    "type": "connected",
                    "client_id": "Python_Visualizer",
                    "version": "1.0.0"
                }))

                print(f"✓ Connected to {uri}")

                # Start receiving messages
                await self.receive_messages()

                # If we get here, connection was closed normally
                break

            except Exception as e:
                retry_count += 1
                if retry_count == 1:
                    self.connection_status.emit(f"Waiting for server...")
                    print(f"Waiting for server to start...")

                # Wait before retrying
                await asyncio.sleep(retry_delay)

        # Connection ended
        self.connection_status.emit("Disconnected")
        print("Connection ended")

    async def receive_messages(self):
        """Receive and process messages"""
        try:
            async for message in self.websocket:
                data = json.loads(message)
                await self.handle_message(data)
        except Exception as e:
            print(f"Receive error: {e}")
            self.connection_status.emit("Disconnected")

    async def handle_message(self, data):
        """Handle received message"""
        msg_type = data.get("type")

        if msg_type == "launch_firework":
            # Extract firework data
            self.firework_received.emit(data)

        elif msg_type == "heartbeat":
            # Respond to heartbeat
            if self.websocket:
                await self.websocket.send(json.dumps({
                    "type": "heartbeat_response",
                    "timestamp": data.get("timestamp")
                }))

        elif msg_type == "reset":
            # Clear all fireworks
            pass

    def disconnect(self):
        """Disconnect from server"""
        self.running = False
        if self.loop and self.websocket:
            asyncio.run_coroutine_threadsafe(self.websocket.close(), self.loop)


class VisualizerWindow(QMainWindow):
    """Main visualizer window"""

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Python Firework Visualizer - Testing Client")
        self.setGeometry(100, 100, 1200, 800)

        # Create central widget
        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)

        # Status label
        self.status_label = QLabel("Status: Not Connected")
        self.status_label.setStyleSheet("""
            QLabel {
                background-color: #1a1a1a;
                color: white;
                padding: 10px;
                font-size: 14px;
                font-weight: bold;
            }
        """)
        layout.addWidget(self.status_label)

        # Canvas
        self.canvas = VisualizerCanvas()
        layout.addWidget(self.canvas)

        # Info label
        info = QLabel("Python Visualizer - Press ESC to exit")
        info.setStyleSheet("""
            QLabel {
                background-color: #1a1a1a;
                color: #888;
                padding: 5px;
                font-size: 11px;
            }
        """)
        info.setAlignment(Qt.AlignCenter)
        layout.addWidget(info)

        # WebSocket client
        self.ws_client = WebSocketClient()
        self.ws_client.firework_received.connect(self.on_firework_received)
        self.ws_client.connection_status.connect(self.on_connection_status)

        # Connect to server after a short delay (let window show first)
        QTimer.singleShot(500, lambda: self.ws_client.start_connection())

    def on_firework_received(self, message):
        """Handle received firework data"""
        try:
            # Extract the actual data from the message
            # Message format: {"type": "launch_firework", "timestamp": ..., "data": {...}}
            firework_data = message.get("data", message)

            # Extract data
            shell_name = firework_data.get("shell_name", "Unknown")

            # Get physics data
            physics = firework_data.get("physics", {})
            launch_angle = physics.get("launch_angle", 0)

            # Get color
            colors = firework_data.get("colors", {})
            primary = colors.get("primary", {"r": 255, "g": 215, "b": 0})
            color = (primary["r"], primary["g"], primary["b"])

            # Get star count
            visual = firework_data.get("visual", {})
            star_count = visual.get("star_count", 100)

            # Add firework to canvas
            self.canvas.add_firework(launch_angle, color, star_count)

            # Update status
            self.status_label.setText(
                f"Status: Connected | Last: {shell_name} @ {launch_angle}° | "
                f"Active: {len(self.canvas.fireworks)}"
            )

            print(f"✓ Received: {shell_name} at angle {launch_angle}° with {star_count} stars")

        except Exception as e:
            print(f"Error processing firework: {e}")
            import traceback
            traceback.print_exc()

    def on_connection_status(self, status):
        """Handle connection status change"""
        self.status_label.setText(f"Status: {status}")

        if "Connected" in status and "attempt" not in status:
            # Successfully connected - green
            self.status_label.setStyleSheet("""
                QLabel {
                    background-color: #1a4d1a;
                    color: white;
                    padding: 10px;
                    font-size: 14px;
                    font-weight: bold;
                }
            """)
        elif "Waiting" in status or "attempt" in status:
            # Waiting/retrying - yellow
            self.status_label.setStyleSheet("""
                QLabel {
                    background-color: #4d4d1a;
                    color: white;
                    padding: 10px;
                    font-size: 14px;
                    font-weight: bold;
                }
            """)
        else:
            # Error or disconnected - red
            self.status_label.setStyleSheet("""
                QLabel {
                    background-color: #4d1a1a;
                    color: white;
                    padding: 10px;
                    font-size: 14px;
                    font-weight: bold;
                }
            """)

    def keyPressEvent(self, event):
        """Handle key press"""
        if event.key() == Qt.Key_Escape:
            self.close()

    def closeEvent(self, event):
        """Handle window close"""
        self.ws_client.disconnect()
        event.accept()


def main():
    """Main entry point"""
    app = QApplication(sys.argv)

    # Create and show window
    window = VisualizerWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()