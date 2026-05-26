from __future__ import annotations
from PyQt6.QtWidgets import QComboBox, QFormLayout, QWizardPage


class LocalePage(QWizardPage):
    def __init__(self) -> None:
        super().__init__()
        self.setTitle("Locale and time")
        self.timezone = QComboBox()
        self.timezone.addItems([
            "UTC", "Asia/Kuala_Lumpur", "Asia/Singapore",
            "America/New_York", "Europe/London",
        ])
        self.keymap = QComboBox()
        self.keymap.addItems(["us", "uk", "de", "fr"])

        form = QFormLayout(self)
        form.addRow("Timezone:", self.timezone)
        form.addRow("Keymap:", self.keymap)

        self.registerField("timezone", self.timezone, "currentText")
        self.registerField("keymap", self.keymap, "currentText")
