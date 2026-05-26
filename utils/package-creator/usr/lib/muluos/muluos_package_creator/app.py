"""Standalone window for the package creator."""
from __future__ import annotations
import sys

from PyQt6.QtWidgets import QApplication, QMainWindow

from .widget import PackageCreatorWidget


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("MuluOS Package Creator")
    win = QMainWindow()
    win.setWindowTitle("MuluOS Package Creator")
    win.setCentralWidget(PackageCreatorWidget())
    win.resize(760, 720)
    win.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
