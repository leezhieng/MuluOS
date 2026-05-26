"""Application manager widget — list installed bundles and uninstall them."""
from __future__ import annotations
import json
import re
import subprocess
from pathlib import Path

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtWidgets import (
    QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QMessageBox,
    QPushButton, QVBoxLayout, QWidget,
)

import muluos_registry as reg

UNINSTALL_HELPER = "/usr/libexec/muluos/app-uninstall"
SYSTEM_BUNDLE = "muluos.system"
_SIZE_RE = re.compile(r"(\d+)")


class AppManagerWidget(QWidget):
    def __init__(self) -> None:
        super().__init__()
        try:
            self._client = reg.Client.connect_direct()
        except OSError as e:
            self._client = None
            layout = QVBoxLayout(self)
            layout.addWidget(QLabel(
                "Registry daemon is not reachable. Start muluos-registryd first.\n"
                f"({e})"
            ))
            return
        self._build_ui()
        self._reload()

    def _build_ui(self) -> None:
        self.list = QListWidget()
        self.list.setIconSize(QSize(48, 48))
        self.list.itemSelectionChanged.connect(self._update_buttons)

        self.uninstall_btn = QPushButton("Uninstall")
        self.uninstall_btn.clicked.connect(self._uninstall)
        self.uninstall_btn.setEnabled(False)
        refresh = QPushButton("Refresh")
        refresh.clicked.connect(self._reload)

        btns = QHBoxLayout()
        btns.addWidget(refresh)
        btns.addStretch()
        btns.addWidget(self.uninstall_btn)

        v = QVBoxLayout(self)
        v.addWidget(QLabel("Installed applications:"))
        v.addWidget(self.list)
        v.addLayout(btns)

    def _bundles(self) -> list[dict]:
        out = []
        for b in self._client.list_bundles():
            if b["id"] == SYSTEM_BUNDLE:
                continue
            bundle = Path(b["path"])
            info = {}
            ipath = bundle / "Info.json"
            if ipath.is_file():
                try:
                    info = json.loads(ipath.read_text(encoding="utf-8"))
                except (json.JSONDecodeError, OSError):
                    info = {}
            out.append({"id": b["id"], "path": bundle, "info": info})
        return out

    def _reload(self) -> None:
        self.list.clear()
        for entry in self._bundles():
            info = entry["info"]
            name = info.get("name", entry["id"])
            version = info.get("version", "")
            label = f"{name}  {version}".strip() + f"\n{entry['path']}"
            item = QListWidgetItem(label)
            icon = self._icon_for(entry)
            if icon:
                item.setIcon(icon)
            item.setData(Qt.ItemDataRole.UserRole, entry)
            self.list.addItem(item)
        self._update_buttons()

    def _icon_for(self, entry: dict) -> QIcon | None:
        icons = entry["path"] / "Resources" / "icons"
        if icons.is_dir():
            candidates = []
            for p in icons.glob("*.png"):
                m = _SIZE_RE.match(p.name)
                if m:
                    candidates.append((int(m.group(1)), p))
            if candidates:
                big = sorted(c for c in candidates if c[0] >= 48)
                chosen = big[0][1] if big else max(candidates)[1]
                pm = QPixmap(str(chosen))
                if not pm.isNull():
                    return QIcon(pm)
        ref = entry["info"].get("icon")
        if ref:
            p = entry["path"] / ref
            if p.is_file():
                return QIcon(str(p))
        return None

    def _update_buttons(self) -> None:
        self.uninstall_btn.setEnabled(bool(self.list.selectedItems()))

    def _uninstall(self) -> None:
        items = self.list.selectedItems()
        if not items:
            return
        entry = items[0].data(Qt.ItemDataRole.UserRole)
        name = entry["info"].get("name", entry["id"])
        if QMessageBox.question(
                self, "Uninstall",
                f"Uninstall {name}?\n\nThis removes the application, its registry "
                "data, and runs any custom uninstall steps it declares.",
        ) != QMessageBox.StandardButton.Yes:
            return
        rc = subprocess.call(["pkexec", UNINSTALL_HELPER, entry["id"]])
        if rc == 0:
            QMessageBox.information(self, "Uninstalled", f"{name} was removed.")
        else:
            QMessageBox.critical(self, "Uninstall failed", f"Exit code {rc}.")
        self._reload()
