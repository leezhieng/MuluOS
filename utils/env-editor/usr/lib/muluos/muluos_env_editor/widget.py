"""Environment editor widget — manages PATH additions and env vars in the
SQLite-backed registry, then regenerates /etc/profile.d/muluos-env.sh."""
from __future__ import annotations
import subprocess

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QAbstractItemView, QFileDialog, QHBoxLayout, QLabel, QListWidget,
    QMessageBox, QPushButton, QTabWidget, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget,
)

import muluos_registry as reg

SYSTEM_BUNDLE = "muluos.system"
ENV_GENERATE = "/usr/libexec/muluos/env-generate"
PATH_KEY = "env.path"
VAR_PREFIX = "env.var."


class EnvEditorWidget(QWidget):
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
        self._load()

    def _build_ui(self) -> None:
        tabs = QTabWidget()
        tabs.addTab(self._build_path_tab(), "PATH")
        tabs.addTab(self._build_vars_tab(), "Variables")

        apply_btn = QPushButton("Apply")
        apply_btn.clicked.connect(self._apply)

        outer = QVBoxLayout(self)
        outer.addWidget(tabs)
        outer.addWidget(apply_btn, alignment=Qt.AlignmentFlag.AlignRight)

    def _build_path_tab(self) -> QWidget:
        self.path_list = QListWidget()
        self.path_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)

        btns = QVBoxLayout()
        for label, slot in [("Add…", self._path_add), ("Remove", self._path_remove),
                            ("Up", self._path_up), ("Down", self._path_down)]:
            b = QPushButton(label)
            b.clicked.connect(slot)
            btns.addWidget(b)
        btns.addStretch()

        row = QHBoxLayout()
        row.addWidget(self.path_list)
        row.addLayout(btns)

        w = QWidget()
        v = QVBoxLayout(w)
        v.addWidget(QLabel("Directories prepended to PATH (top = highest priority):"))
        v.addLayout(row)
        return w

    def _build_vars_tab(self) -> QWidget:
        self.var_table = QTableWidget(0, 2)
        self.var_table.setHorizontalHeaderLabels(["Name", "Value"])
        self.var_table.horizontalHeader().setStretchLastSection(True)

        btns = QHBoxLayout()
        add = QPushButton("Add")
        add.clicked.connect(self._var_add)
        rm = QPushButton("Remove")
        rm.clicked.connect(self._var_remove)
        btns.addWidget(add)
        btns.addWidget(rm)
        btns.addStretch()

        w = QWidget()
        v = QVBoxLayout(w)
        v.addWidget(self.var_table)
        v.addLayout(btns)
        return w

    def _load(self) -> None:
        raw = self._client.machine_get(SYSTEM_BUNDLE, PATH_KEY, "") or ""
        self.path_list.clear()
        for d in [p for p in raw.split(":") if p]:
            self.path_list.addItem(d)

        self.var_table.setRowCount(0)
        for item in self._client.machine_list(SYSTEM_BUNDLE, prefix=VAR_PREFIX):
            name = item["key"][len(VAR_PREFIX):]
            self._append_var_row(name, str(item["value"]))

    def _append_var_row(self, name: str = "", value: str = "") -> None:
        r = self.var_table.rowCount()
        self.var_table.insertRow(r)
        self.var_table.setItem(r, 0, QTableWidgetItem(name))
        self.var_table.setItem(r, 1, QTableWidgetItem(value))

    def _var_add(self) -> None:
        self._append_var_row()

    def _var_remove(self) -> None:
        r = self.var_table.currentRow()
        if r >= 0:
            self.var_table.removeRow(r)

    def _path_add(self) -> None:
        d = QFileDialog.getExistingDirectory(self, "Select directory to add to PATH")
        if d:
            self.path_list.addItem(d)

    def _path_remove(self) -> None:
        r = self.path_list.currentRow()
        if r >= 0:
            self.path_list.takeItem(r)

    def _path_up(self) -> None:
        r = self.path_list.currentRow()
        if r > 0:
            self.path_list.insertItem(r - 1, self.path_list.takeItem(r))
            self.path_list.setCurrentRow(r - 1)

    def _path_down(self) -> None:
        r = self.path_list.currentRow()
        if 0 <= r < self.path_list.count() - 1:
            self.path_list.insertItem(r + 1, self.path_list.takeItem(r))
            self.path_list.setCurrentRow(r + 1)

    def _apply(self) -> None:
        dirs = [self.path_list.item(i).text() for i in range(self.path_list.count())]
        self._client.machine_set(SYSTEM_BUNDLE, PATH_KEY, ":".join(dirs))

        existing = {item["key"][len(VAR_PREFIX):]
                    for item in self._client.machine_list(SYSTEM_BUNDLE, prefix=VAR_PREFIX)}
        current: dict[str, str] = {}
        for r in range(self.var_table.rowCount()):
            name_item = self.var_table.item(r, 0)
            val_item = self.var_table.item(r, 1)
            name = (name_item.text() if name_item else "").strip()
            if not name:
                continue
            current[name] = val_item.text() if val_item else ""

        for name, value in current.items():
            self._client.machine_set(SYSTEM_BUNDLE, VAR_PREFIX + name, value)
        for name in existing - set(current):
            try:
                self._client.machine_delete(SYSTEM_BUNDLE, VAR_PREFIX + name)
            except reg.RegistryError:
                pass

        try:
            subprocess.check_call([ENV_GENERATE])
        except (FileNotFoundError, subprocess.CalledProcessError) as e:
            QMessageBox.critical(self, "env-generate failed", str(e))
            return
        QMessageBox.information(
            self, "Applied",
            "Environment saved. Changes take effect on next login\n"
            "(or run: source /etc/profile.d/muluos-env.sh).",
        )
