from __future__ import annotations
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWizardPage


class WelcomePage(QWizardPage):
    def __init__(self) -> None:
        super().__init__()
        self.setTitle("Welcome to MuluOS")
        self.setSubTitle("This wizard will install MuluOS on your system.")
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(
            "Make sure you have backed up any important data before continuing."
        ))
