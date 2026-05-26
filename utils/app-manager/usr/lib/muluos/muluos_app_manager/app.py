"""Standalone window for the application manager."""
from __future__ import annotations
import sys

from PyQt6.QtWidgets import QApplication, QMainWindow

from .widget import AppManagerWidget


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("MuluOS Add or Remove Programs")
    win = QMainWindow()
    win.setWindowTitle("Add or Remove Programs")
    win.setCentralWidget(AppManagerWidget())
    win.resize(680, 520)
    win.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
