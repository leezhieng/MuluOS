from __future__ import annotations
from PyQt6.QtWidgets import QFormLayout, QLineEdit, QWizardPage


class UserPage(QWizardPage):
    def __init__(self) -> None:
        super().__init__()
        self.setTitle("Create your user")
        self.username = QLineEdit()
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_confirm = QLineEdit()
        self.password_confirm.setEchoMode(QLineEdit.EchoMode.Password)
        self.hostname = QLineEdit("muluos")

        form = QFormLayout(self)
        form.addRow("Username:", self.username)
        form.addRow("Password:", self.password)
        form.addRow("Confirm:", self.password_confirm)
        form.addRow("Hostname:", self.hostname)

        self.registerField("username*", self.username)
        self.registerField("password*", self.password)
        self.registerField("hostname*", self.hostname)

    def validatePage(self) -> bool:
        return self.password.text() == self.password_confirm.text()
