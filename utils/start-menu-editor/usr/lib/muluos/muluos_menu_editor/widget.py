"""Start Menu editor widget — shared by the standalone utility and the
Settings panel. Reads/writes menu data through the SQLite-backed registry."""
from __future__ import annotations
import subprocess

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox, QDialog, QDialogButtonBox, QFormLayout, QHBoxLayout, QLabel,
    QLineEdit, QListWidget, QListWidgetItem, QMessageBox, QPushButton,
    QSpinBox, QSplitter, QVBoxLayout, QWidget,
)

import muluos_registry as reg

SYSTEM_BUNDLE = "muluos.system"
MENU_SYNC = "/usr/libexec/muluos/menu-sync"


class MenuEditorWidget(QWidget):
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
        self._reload_categories()

    def _build_ui(self) -> None:
        self.cat_list = QListWidget()
        self.cat_list.itemSelectionChanged.connect(self._reload_programs)

        cat_btns = QHBoxLayout()
        for label, slot in [("Add", self._add_category),
                            ("Edit", self._edit_category),
                            ("Delete", self._delete_category)]:
            b = QPushButton(label)
            b.clicked.connect(slot)
            cat_btns.addWidget(b)

        cat_box = QWidget()
        cv = QVBoxLayout(cat_box)
        cv.addWidget(QLabel("Categories"))
        cv.addWidget(self.cat_list)
        cv.addLayout(cat_btns)

        self.prog_list = QListWidget()
        prog_btns = QHBoxLayout()
        edit_b = QPushButton("Edit assignment")
        edit_b.clicked.connect(self._edit_program)
        hide_b = QPushButton("Toggle hidden")
        hide_b.clicked.connect(self._toggle_hidden)
        prog_btns.addWidget(edit_b)
        prog_btns.addWidget(hide_b)

        prog_box = QWidget()
        pv = QVBoxLayout(prog_box)
        pv.addWidget(QLabel("Programs in selected category"))
        pv.addWidget(self.prog_list)
        pv.addLayout(prog_btns)

        split = QSplitter()
        split.addWidget(cat_box)
        split.addWidget(prog_box)
        split.setSizes([360, 540])

        apply_btn = QPushButton("Apply changes to menu")
        apply_btn.clicked.connect(self._sync_menu)

        outer = QVBoxLayout(self)
        outer.addWidget(split)
        outer.addWidget(apply_btn, alignment=Qt.AlignmentFlag.AlignRight)

    def _categories(self) -> list[dict]:
        keys = self._client.machine_list(SYSTEM_BUNDLE, prefix="menu.category.")
        by_id: dict[str, dict] = {}
        for k in keys:
            parts = k["key"].split(".")
            if len(parts) < 4:
                continue
            cid, field = parts[2], parts[3]
            by_id.setdefault(cid, {"id": cid, "name": cid, "icon": "", "order": 999})
            by_id[cid][field] = k["value"]
        return sorted(by_id.values(), key=lambda c: (int(c.get("order", 999)), c["id"]))

    def _reload_categories(self) -> None:
        self.cat_list.clear()
        for c in self._categories():
            item = QListWidgetItem(f"{c['name']}  ({c['id']})")
            item.setData(Qt.ItemDataRole.UserRole, c)
            self.cat_list.addItem(item)
        if self.cat_list.count():
            self.cat_list.setCurrentRow(0)

    def _reload_programs(self) -> None:
        self.prog_list.clear()
        cat = self._selected_category()
        if not cat:
            return
        for b in self._client.list_bundles():
            if b["id"] == SYSTEM_BUNDLE:
                continue
            meta = {item["key"]: item["value"]
                    for item in self._client.machine_list(b["id"], prefix="menu.")}
            if meta.get("menu.category") != cat["id"]:
                continue
            label = meta.get("menu.name", b["id"])
            if meta.get("menu.hidden"):
                label = f"{label}  [hidden]"
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, {**b, "meta": meta})
            self.prog_list.addItem(item)

    def _selected_category(self) -> dict | None:
        items = self.cat_list.selectedItems()
        return items[0].data(Qt.ItemDataRole.UserRole) if items else None

    def _add_category(self) -> None:
        dlg = _CategoryDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._write_category(dlg.values())
            self._reload_categories()

    def _edit_category(self) -> None:
        cat = self._selected_category()
        if not cat:
            return
        dlg = _CategoryDialog(self, initial=cat)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            new = dlg.values()
            if new["id"] != cat["id"]:
                self._delete_category_keys(cat["id"])
            self._write_category(new)
            self._reload_categories()

    def _delete_category(self) -> None:
        cat = self._selected_category()
        if not cat:
            return
        msg = f"Delete category '{cat['name']}'?\nPrograms in it will be unassigned from the menu."
        if QMessageBox.question(self, "Delete category", msg) != QMessageBox.StandardButton.Yes:
            return
        self._delete_category_keys(cat["id"])
        self._reload_categories()

    def _write_category(self, cat: dict) -> None:
        cid = cat["id"]
        self._client.machine_set(SYSTEM_BUNDLE, f"menu.category.{cid}.name", cat["name"])
        self._client.machine_set(SYSTEM_BUNDLE, f"menu.category.{cid}.icon", cat["icon"])
        self._client.machine_set(SYSTEM_BUNDLE, f"menu.category.{cid}.order", int(cat["order"]), type="int")

    def _delete_category_keys(self, cid: str) -> None:
        for field in ("name", "icon", "order"):
            try:
                self._client.machine_delete(SYSTEM_BUNDLE, f"menu.category.{cid}.{field}")
            except reg.RegistryError:
                pass

    def _edit_program(self) -> None:
        items = self.prog_list.selectedItems()
        if not items:
            return
        prog = items[0].data(Qt.ItemDataRole.UserRole)
        dlg = _ProgramDialog(self, prog, self._categories())
        if dlg.exec() == QDialog.DialogCode.Accepted:
            new = dlg.values()
            self._client.machine_set(prog["id"], "menu.name", new["name"])
            self._client.machine_set(prog["id"], "menu.icon", new["icon"])
            self._client.machine_set(prog["id"], "menu.category", new["category"])
            self._reload_programs()

    def _toggle_hidden(self) -> None:
        items = self.prog_list.selectedItems()
        if not items:
            return
        prog = items[0].data(Qt.ItemDataRole.UserRole)
        current = bool(prog["meta"].get("menu.hidden", False))
        self._client.machine_set(prog["id"], "menu.hidden", not current, type="bool")
        self._reload_programs()

    def _sync_menu(self) -> None:
        try:
            subprocess.check_call([MENU_SYNC])
        except (FileNotFoundError, subprocess.CalledProcessError) as e:
            QMessageBox.critical(self, "Menu sync failed", str(e))
            return
        QMessageBox.information(self, "Menu sync",
                                "Start menu updated. Plasma may take a moment to refresh.")


class _CategoryDialog(QDialog):
    def __init__(self, parent: QWidget, initial: dict | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Category")
        self.id = QLineEdit(initial["id"] if initial else "")
        self.name = QLineEdit((initial or {}).get("name", ""))
        self.icon = QLineEdit((initial or {}).get("icon", ""))
        self.order = QSpinBox()
        self.order.setRange(0, 9999)
        self.order.setValue(int((initial or {}).get("order", 100)))

        form = QFormLayout()
        form.addRow("ID:", self.id)
        form.addRow("Name:", self.name)
        form.addRow("Icon:", self.icon)
        form.addRow("Order:", self.order)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def values(self) -> dict:
        return {
            "id": self.id.text().strip(),
            "name": self.name.text().strip(),
            "icon": self.icon.text().strip(),
            "order": self.order.value(),
        }


class _ProgramDialog(QDialog):
    def __init__(self, parent: QWidget, prog: dict, categories: list[dict]) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"Menu entry: {prog['id']}")
        meta = prog["meta"]
        self.name = QLineEdit(meta.get("menu.name", prog["id"]))
        self.icon = QLineEdit(meta.get("menu.icon", ""))
        self.category = QComboBox()
        for c in categories:
            self.category.addItem(c["name"], userData=c["id"])
        cur = meta.get("menu.category")
        if cur:
            idx = self.category.findData(cur)
            if idx >= 0:
                self.category.setCurrentIndex(idx)

        form = QFormLayout()
        form.addRow("Name:", self.name)
        form.addRow("Icon:", self.icon)
        form.addRow("Category:", self.category)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def values(self) -> dict:
        return {
            "name": self.name.text().strip(),
            "icon": self.icon.text().strip(),
            "category": self.category.currentData(),
        }
