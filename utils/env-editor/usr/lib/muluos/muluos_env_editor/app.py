"""Standalone window for the Environment editor."""
from __future__ import annotations
import sys

from PyQt6.QtWidgets import QApplication, QMainWindow

from .widget import EnvEditorWidget


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("MuluOS Environment Editor")
    win = QMainWindow()
    win.setWindowTitle("MuluOS Environment Editor")
    win.setCentralWidget(EnvEditorWidget())
    win.resize(720, 520)
    win.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
