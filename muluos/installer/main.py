"""Installer entry point. Launched by the live session."""
from __future__ import annotations
import sys

from PyQt6.QtWidgets import QApplication, QWizard

from .pages import disk, locale, summary, user, welcome


def build_wizard() -> QWizard:
    wiz = QWizard()
    wiz.setWindowTitle("MuluOS Installer")
    wiz.addPage(welcome.WelcomePage())
    wiz.addPage(locale.LocalePage())
    wiz.addPage(disk.DiskPage())
    wiz.addPage(user.UserPage())
    wiz.addPage(summary.SummaryPage())
    wiz.resize(720, 480)
    return wiz


def main() -> int:
    app = QApplication(sys.argv)
    wiz = build_wizard()
    wiz.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
