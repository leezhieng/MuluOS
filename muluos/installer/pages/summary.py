from __future__ import annotations
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWizardPage

from ..backend import bootloader, fmt, install, partition


class SummaryPage(QWizardPage):
    def __init__(self) -> None:
        super().__init__()
        self.setTitle("Ready to install")
        self.label = QLabel()
        self.label.setWordWrap(True)
        layout = QVBoxLayout(self)
        layout.addWidget(self.label)

    def initializePage(self) -> None:
        self.label.setText(
            f"Disk:     {self.field('disk')}\n"
            f"User:     {self.field('username')}\n"
            f"Hostname: {self.field('hostname')}\n"
            f"Timezone: {self.field('timezone')}\n"
            f"Keymap:   {self.field('keymap')}\n\n"
            "Press Finish to begin. THIS WILL ERASE THE TARGET DISK."
        )

    def validatePage(self) -> bool:
        cfg = {
            "disk": self.field("disk"),
            "username": self.field("username"),
            "password": self.field("password"),
            "hostname": self.field("hostname"),
            "timezone": self.field("timezone"),
            "keymap": self.field("keymap"),
        }
        partition.partition(cfg["disk"])
        fmt.format_partitions(cfg["disk"])
        install.copy_rootfs(cfg["disk"], cfg)
        bootloader.install(cfg["disk"])
        return True
