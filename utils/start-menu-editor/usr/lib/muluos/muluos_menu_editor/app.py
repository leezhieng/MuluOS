"""Standalone window for the Start Menu editor."""
from __future__ import annotations
import sys

from PyQt6.QtWidgets import QApplication, QMainWindow

from .widget import MenuEditorWidget


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("MuluOS Start Menu Editor")
    win = QMainWindow()
    win.setWindowTitle("MuluOS Start Menu Editor")
    win.setCentralWidget(MenuEditorWidget())
    win.resize(940, 620)
    win.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
