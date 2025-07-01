import sys
import asyncio
import os
from PySide6.QtWidgets import QApplication
from views.main_window import MainWindow
from PySide6.QtAsyncio.events import QAsyncioEventLoop

# Suppress Qt layer-backing warnings on macOS
os.environ["QT_MAC_WANTS_LAYER"] = "1"


def main():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    loop = QAsyncioEventLoop(app)
    asyncio.set_event_loop(loop)

    window = MainWindow()
    window.show()

    loop.run_forever()


if __name__ == "__main__":
    main()
