import os
from pathlib import Path
from PySide6.QtWidgets import (QWidget, QPushButton, QVBoxLayout, QHBoxLayout,
                               QLabel, QSizePolicy, QSpacerItem, QFileDialog,
                               QMenu)
from PySide6.QtGui import QPixmap, QPalette, QBrush, QFont, QIcon, QTransform, QAction
from PySide6.QtCore import Qt, QSize, Signal, QEvent


class WelcomePage(QWidget):
    """
    Welcome page with background image and three main action buttons
    """
    # Define signals for button clicks
    design_show_clicked = Signal()
    load_show_clicked = Signal()
    import_show_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("CUE MANAGEMENT SYSTEM")

        # Resolve background image relative to project images directory
        images_dir = Path(__file__).resolve().parent.parent / "images"

        # Try preferred filenames (case variations) first
        preferred_names = [
            "CuePiShifter_logo.png",
            "CuePiShifter_logo.PNG",
            "cuepishifter_logo.png",
            "cuepishifter_logo.PNG",
        ]

        found_path = None
        for name in preferred_names:
            candidate = images_dir / name
            if candidate.exists():
                found_path = candidate
                break

        # If not found, try any png/jpg in images folder that looks like a logo/background
        if not found_path and images_dir.exists():
            for p in images_dir.iterdir():
                if p.is_file() and p.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".bmp"}:
                    if "logo" in p.name.lower() or "background" in p.name.lower():
                        found_path = p
                        break

        # Set the background path (string) if found; leave empty to trigger fallback logic
        self.background_image_path = str(found_path) if found_path else ""

        # Alternative paths to try if the main path doesn't work (search other images in the images folder)
        self.alternative_paths = []
        if images_dir.exists():
            for p in images_dir.iterdir():
                if p.is_file() and p.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".bmp"}:
                    # Avoid duplicating the found_path
                    if str(p) != self.background_image_path:
                        self.alternative_paths.append(str(p))

        # Set up the background image
        self.setup_background()

        # Create the layout and buttons
        self.setup_ui()

        # Install event filter for resize events
        self.installEventFilter(self)

    def setup_background(self):
        """Set up the background image for the welcome page"""
        # Try the main path first
        if os.path.exists(self.background_image_path):
            print(f"Loading background image from: {self.background_image_path}")
            self.update_background_image()
            return

        # If main path fails, try alternative paths
        for alt_path in self.alternative_paths:
            if os.path.exists(alt_path):
                print(f"Loading background image from alternative path: {alt_path}")
                self.background_image_path = alt_path
                self.update_background_image()
                return

        # If all paths fail, try to find the image in the current directory
        current_dir = os.getcwd()
        for file in os.listdir(current_dir):
            if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')) and (
                    'logo' in file.lower() or 'background' in file.lower()):
                print(f"Found potential logo image in current directory: {file}")
                self.background_image_path = os.path.join(current_dir, file)
                self.update_background_image()
                return

        # If all attempts fail, prompt the user to select an image
        self.prompt_for_background_image()

    def prompt_for_background_image(self):
        """Prompt the user to select a background image"""
        # Create a simple dialog to inform the user
        print("Prompting user to select a background image...")

        # Create a file dialog to select an image
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Background Image",
            "",
            "Image Files (*.png *.jpg *.jpeg *.gif *.bmp)"
        )

        if file_path:
            print(f"User selected background image: {file_path}")
            self.background_image_path = file_path
            self.update_background_image()
        else:
            print("No image selected. Using fallback color.")
            self.setStyleSheet("background-color: #2c3e50;")

    def update_background_image(self):
        """Update the background image based on current window size"""
        try:
            # Set a solid black background first
            self.setStyleSheet("background-color: #000000;")

            # Try to load the image
            pixmap = QPixmap(self.background_image_path)

            if pixmap.isNull():
                print(f"Error: Failed to load the background image from {self.background_image_path}")
                # Try to load the image using a different method
                try:
                    image_file = open(self.background_image_path, 'rb')
                    image_data = image_file.read()
                    image_file.close()

                    pixmap = QPixmap()
                    if not pixmap.loadFromData(image_data):
                        print("Error: Failed to load image from binary data")
                        return
                except Exception as e:
                    print(f"Error loading image data: {str(e)}")
                    return

            print(f"Image loaded successfully. Size: {pixmap.width()}x{pixmap.height()}")

            # Instead of using a brush pattern which can cause tiling/duplication,
            # we'll create a single centered image label

            # Remove any existing background label
            for child in self.findChildren(QLabel, "background_label"):
                child.deleteLater()

            # Create a new label for the background image
            background_label = QLabel(self)
            background_label.setObjectName("background_label")

            # Size the image appropriately - make it smaller (25% smaller than original)
            window_width = self.width()
            image_width = int(window_width * 0.45)  # 45% of window width (25% smaller than original 60%)

            # Scale the image proportionally
            scaled_pixmap = pixmap.scaled(
                image_width,
                int(pixmap.height() * image_width / pixmap.width()),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )

            # Set the scaled image to the label
            background_label.setPixmap(scaled_pixmap)

            # Center the label horizontally
            background_label.setAlignment(Qt.AlignCenter)

            # Position the label - centered horizontally, positioned vertically
            background_label.setGeometry(
                (self.width() - scaled_pixmap.width()) // 2,  # Center horizontally
                self.height() // 2 - scaled_pixmap.height() // 2 - 120,  # Even higher vertical position
                scaled_pixmap.width(),
                scaled_pixmap.height()
            )

            # Make sure the label is behind other widgets
            background_label.lower()

            # Show the label
            background_label.show()

            print(f"Successfully set background image from: {self.background_image_path}")

        except Exception as e:
            print(f"Error setting background image: {str(e)}")
            self.setStyleSheet("background-color: #000000;")

    def setup_ui(self):
        """Set up the UI components"""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(50, 20, 50, 50)  # Reduced top margin

        # Add a title at the top - positioned to be visible with the background image
        title_label = QLabel("Cue Management System")
        title_label.setAlignment(Qt.AlignCenter)
        title_font = QFont("Arial", 48, QFont.Bold)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: white;")
        main_layout.addWidget(title_label)

        # Add subtitle
        subtitle_label = QLabel("Professional Pyrotechnic Control System")
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_font = QFont("Arial", 24)
        subtitle_label.setFont(subtitle_font)
        subtitle_label.setStyleSheet("color: #f0f0f0;")
        main_layout.addWidget(subtitle_label)

        # Add a large spacer to push buttons to the bottom
        # This will position buttons below the image
        main_layout.addItem(
            QSpacerItem(20, 500, QSizePolicy.Minimum, QSizePolicy.Expanding))  # Adjusted to 500px for smaller image

        # Create a horizontal layout for the buttons with center alignment
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setSpacing(50)  # More spacing between buttons
        button_layout.setContentsMargins(100, 0, 100, 0)  # Add horizontal margins

        # Create the three main buttons
        self.design_button = self.create_button("DESIGN SHOW", "#1e5631")
        self.load_button = self.create_button("LOAD SHOW", "#1e3d6e")
        self.import_button = self.create_button("IMPORT SHOW", "#8b0000")

        # Add buttons to the layout
        button_layout.addWidget(self.design_button)
        button_layout.addWidget(self.load_button)
        button_layout.addWidget(self.import_button)

        # Add button container to main layout
        main_layout.addWidget(button_container, alignment=Qt.AlignCenter)

        # Add a larger spacer at the bottom to position buttons correctly
        main_layout.addItem(QSpacerItem(20, 80, QSizePolicy.Minimum, QSizePolicy.Fixed))

        # Connect button signals
        self.design_button.clicked.connect(self.design_show_clicked.emit)
        self.load_button.clicked.connect(self.load_show_clicked.emit)
        self.import_button.clicked.connect(self.import_show_clicked.emit)

    def eventFilter(self, obj, event):
        """Event filter to handle resize events and context menu events"""
        if obj == self:
            if event.type() == QEvent.Resize:
                # Update background image when window is resized
                # Use a small delay to ensure the window is fully resized
                from PySide6.QtCore import QTimer
                QTimer.singleShot(100, self.update_background_image)
            elif event.type() == QEvent.ContextMenu:
                # Show context menu for right-click
                self.show_context_menu(event.globalPos())
        return super().eventFilter(obj, event)

    def resizeEvent(self, event):
        """Handle resize events"""
        super().resizeEvent(event)
        # Update background image when window is resized
        # Use a small delay to ensure the window is fully resized
        from PySide6.QtCore import QTimer
        QTimer.singleShot(100, self.update_background_image)

    def showEvent(self, event):
        """Handle show event to update background on initial display"""
        super().showEvent(event)
        # Update background when window is first shown
        # Use a small delay to ensure the window is fully sized
        from PySide6.QtCore import QTimer
        QTimer.singleShot(100, self.update_background_image)

    def show_context_menu(self, position):
        """Show context menu for right-click"""
        # Create context menu
        context_menu = QMenu(self)

        # Add actions
        change_bg_action = QAction("Change Background Image", self)
        change_bg_action.triggered.connect(self.prompt_for_background_image)
        context_menu.addAction(change_bg_action)

        # Show the menu
        context_menu.exec_(position)

    def create_button(self, text, color):
        """Create a styled button"""
        button = QPushButton(text)
        button.setMinimumSize(250, 120)  # Larger buttons
        button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        # Style the button - using only supported properties
        button.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: 3px solid white;
                border-radius: 15px;
                padding: 15px;
                font-size: 22px;
                font-weight: bold;
                letter-spacing: 1px;
            }}
            QPushButton:hover {{
                background-color: #333333;
                border: 4px solid white;
                font-size: 24px;
            }}
            QPushButton:pressed {{
                background-color: #555555;
                border: 4px solid #cccccc;
                padding-top: 18px;
                padding-bottom: 12px;
            }}
        """)

        return button