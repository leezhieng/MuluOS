"""Settings shell entry point."""
from __future__ import annotations
import sys

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QApplication, QListWidget, QListWidgetItem, QMainWindow, QSplitter,
    QStackedWidget,
)

from .panel import Panel
from .panels.start_menu import StartMenuPanel


def discover_panels() -> list[Panel]:
    # To add a panel: drop a Panel subclass into .panels and append it here.
    return [
        StartMenuPanel(),
    ]


class SettingsWindow(QMainWindow):
    def __init__(self, panels: list[Panel]) -> None:
        super().__init__()
        self.setWindowTitle("MuluOS Settings")
        self.resize(1000, 640)

        self.sidebar = QListWidget()
        self.sidebar.setIconSize(QSize(24, 24))
        self.sidebar.setFixedWidth(220)
        self.stack = QStackedWidget()

        for p in panels:
            item = QListWidgetItem(QIcon.fromTheme(p.icon_name()), p.title())
            item.setData(Qt.ItemDataRole.UserRole, p)
            self.sidebar.addItem(item)
            self.stack.addWidget(p.widget())

        self.sidebar.currentRowChanged.connect(self.stack.setCurrentIndex)
        self.sidebar.setCurrentRow(0)

        split = QSplitter()
        split.addWidget(self.sidebar)
        split.addWidget(self.stack)
        split.setStretchFactor(0, 0)
        split.setStretchFactor(1, 1)
        self.setCentralWidget(split)


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("MuluOS Settings")
    panels = discover_panels()
    win = SettingsWindow(panels)
    win.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
