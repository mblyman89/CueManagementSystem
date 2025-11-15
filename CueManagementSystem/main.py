import sys
import asyncio
import os
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import QCoreApplication
from views.main_window import MainWindow
from views.welcome_page import WelcomePage
from PySide6.QtAsyncio.events import QAsyncioEventLoop
import logging
from pathlib import Path

log_dir = Path.home() / "Desktop" / "CuePi_Logs"
log_dir.mkdir(exist_ok=True)
log_file = log_dir / "CuePi_debug.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(str(log_file)),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
logger.info("CuePi Application Starting")

# Suppress Qt layer-backing warnings on macOS
os.environ["QT_MAC_WANTS_LAYER"] = "1"

# ============================================================================
# CRITICAL: Set application name for macOS menu bar
# This works both when running from PyCharm AND when running as app bundle
# ============================================================================
if sys.platform.startswith('darwin'):
    # For running directly from Python (PyCharm, terminal, etc.)
    # Use PyObjC to set the app name via Cocoa
    try:
        from Foundation import NSBundle
        bundle = NSBundle.mainBundle()
        if bundle:
            app_name = "CuePiShifter"
            app_info = bundle.localizedInfoDictionary() or bundle.infoDictionary()
            if app_info:
                app_info['CFBundleName'] = app_name
    except ImportError:
        # PyObjC not available, fall back to Qt method (works for app bundles)
        pass

# Also set via Qt (works for app bundles)
QCoreApplication.setApplicationName("CuePiShifter")
QCoreApplication.setOrganizationName("CueManagementSystem")
QCoreApplication.setOrganizationDomain("https://github.com/mblyman89/CueManagementSystem")

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