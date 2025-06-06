import sys
import asyncio
from PySide6.QtWidgets import QApplication
from views.main_window import MainWindow
from qasync import QEventLoop, QApplication


async def main():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    window = MainWindow()
    window.show()

    with loop:
        await loop.run_forever()


if __name__ == "__main__":
    asyncio.run(main())