from __future__ import annotations
from PyQt6.QtWidgets import QComboBox, QFormLayout, QWizardPage

from ..backend import partition


class DiskPage(QWizardPage):
    def __init__(self) -> None:
        super().__init__()
        self.setTitle("Choose a disk")
        self.setSubTitle("The selected disk will be erased.")
        self.disk = QComboBox()
        form = QFormLayout(self)
        form.addRow("Target disk:", self.disk)
        self.registerField("disk*", self.disk, "currentText")

    def initializePage(self) -> None:
        self.disk.clear()
        self.disk.addItems(partition.list_disks())
