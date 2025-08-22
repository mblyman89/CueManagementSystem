import sys
import asyncio
import os
from PySide6.QtWidgets import QApplication, QMessageBox
from views.main_window import MainWindow
from views.welcome_page import WelcomePage
from PySide6.QtAsyncio.events import QAsyncioEventLoop

# Suppress Qt layer-backing warnings on macOS
os.environ["QT_MAC_WANTS_LAYER"] = "1"

class Application:
    def __init__(self):
        self.app = QApplication.instance()
        if self.app is None:
            self.app = QApplication(sys.argv)

        # Set up asyncio event loop
        self.loop = QAsyncioEventLoop(self.app)
        asyncio.set_event_loop(self.loop)

        # Create welcome page first
        self.welcome_page = WelcomePage()
        self.main_window = None

        # Connect welcome page signals
        self.welcome_page.design_show_clicked.connect(self.on_design_show)
        self.welcome_page.load_show_clicked.connect(self.on_load_show)
        self.welcome_page.import_show_clicked.connect(self.on_import_show)

        # Show welcome page
        self.welcome_page.showMaximized()

    def on_design_show(self):
        """Handle Design Show button click"""
        self.open_main_window()

    def on_load_show(self):
        """Handle Load Show button click"""
        self.open_main_window()
        # After main window is open, trigger the load show action
        if self.main_window and hasattr(self.main_window, 'show_manager'):
            self.main_window.show_manager.load_show()

    def on_import_show(self):
        """Handle Import Show button click"""
        self.open_main_window()
        # After main window is open, trigger the import show action
        if self.main_window and hasattr(self.main_window, 'show_manager'):
            self.main_window.show_manager.import_show()

    def open_main_window(self):
        """Open the main application window"""
        if not self.main_window:
            self.main_window = MainWindow()

        # Hide welcome page and show main window
        self.welcome_page.hide()
        self.main_window.showMaximized()

    def run(self):
        """Run the application"""
        # Use asyncio event loop instead of standard Qt event loop
        self.loop.run_forever()


def main():
    app = Application()
    app.run()


if __name__ == "__main__":
    main()