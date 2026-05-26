"""MuluOS package creator widget — build .exe bundles and installers."""
from __future__ import annotations
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QFileDialog, QFormLayout, QGroupBox, QHBoxLayout, QInputDialog, QLabel,
    QLineEdit, QListWidget, QMessageBox, QPushButton, QScrollArea,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from . import builder


class PackageCreatorWidget(QWidget):
    def __init__(self) -> None:
        super().__init__()
        body = QWidget()
        v = QVBoxLayout(body)
        v.addWidget(self._metadata_group())
        v.addWidget(self._executable_group())
        v.addWidget(self._deps_group())
        v.addWidget(self._icon_group())
        v.addWidget(self._env_group())
        v.addWidget(self._uninstall_group())
        v.addWidget(self._output_group())
        v.addStretch()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(body)

        outer = QVBoxLayout(self)
        outer.addWidget(scroll)
        outer.addLayout(self._action_buttons())

    def _metadata_group(self) -> QGroupBox:
        self.id_edit = QLineEdit()
        self.id_edit.setPlaceholderText("com.example.myapp")
        self.name_edit = QLineEdit()
        self.version_edit = QLineEdit("1.0.0")
        self.comment_edit = QLineEdit()
        self.categories_edit = QLineEdit("Utility")
        form = QFormLayout()
        form.addRow("Bundle ID:", self.id_edit)
        form.addRow("Display name:", self.name_edit)
        form.addRow("Version:", self.version_edit)
        form.addRow("Comment:", self.comment_edit)
        form.addRow("Categories:", self.categories_edit)
        box = QGroupBox("Application")
        box.setLayout(form)
        return box

    def _executable_group(self) -> QGroupBox:
        self.exec_edit = QLineEdit()
        self.exec_edit.setReadOnly(True)
        self.exec_edit.setPlaceholderText("Select your compiled executable")
        browse = QPushButton("Browse…")
        browse.clicked.connect(self._pick_exec)
        row = QHBoxLayout()
        row.addWidget(self.exec_edit)
        row.addWidget(browse)
        box = QGroupBox("Executable (pre-compiled)")
        lay = QVBoxLayout(box)
        lay.addWidget(QLabel("MuluOS bundles ship a pre-built binary; no source is compiled."))
        lay.addLayout(row)
        return box

    def _deps_group(self) -> QGroupBox:
        self.dep_list = QListWidget()
        add = QPushButton("Add libraries…")
        add.clicked.connect(self._add_deps)
        auto = QPushButton("Auto-detect (ldd)")
        auto.clicked.connect(self._autodetect_deps)
        rm = QPushButton("Remove")
        rm.clicked.connect(self._remove_dep)
        btns = QHBoxLayout()
        btns.addWidget(add)
        btns.addWidget(auto)
        btns.addWidget(rm)
        btns.addStretch()
        box = QGroupBox("Dependencies (bundled into Contents/lib)")
        lay = QVBoxLayout(box)
        lay.addWidget(self.dep_list)
        lay.addLayout(btns)
        return box

    def _icon_group(self) -> QGroupBox:
        self.icon_edit = QLineEdit()
        self.icon_edit.setReadOnly(True)
        browse = QPushButton("Browse…")
        browse.clicked.connect(self._pick_icon)
        row = QHBoxLayout()
        row.addWidget(self.icon_edit)
        row.addWidget(browse)

        self.icon_preview = QLabel("no icon")
        self.icon_preview.setFixedSize(96, 96)
        self.icon_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.sizes_edit = QLineEdit("16,32,48,64,128,256,512")

        box = QGroupBox("Icon (resized to each size below)")
        lay = QVBoxLayout(box)
        lay.addLayout(row)
        prow = QHBoxLayout()
        prow.addWidget(self.icon_preview)
        prow.addWidget(QLabel("Generated sizes (px):"))
        prow.addWidget(self.sizes_edit)
        prow.addStretch()
        lay.addLayout(prow)
        return box

    def _env_group(self) -> QGroupBox:
        self.env_table = QTableWidget(0, 2)
        self.env_table.setHorizontalHeaderLabels(["Name", "Value"])
        self.env_table.horizontalHeader().setStretchLastSection(True)
        add = QPushButton("Add")
        add.clicked.connect(lambda: self._env_add())
        rm = QPushButton("Remove")
        rm.clicked.connect(self._env_remove)
        btns = QHBoxLayout()
        btns.addWidget(add)
        btns.addWidget(rm)
        btns.addStretch()
        box = QGroupBox("Environment variables")
        lay = QVBoxLayout(box)
        lay.addWidget(self.env_table)
        lay.addLayout(btns)
        return box

    def _uninstall_group(self) -> QGroupBox:
        self.uninstall_hook_edit = QLineEdit()
        self.uninstall_hook_edit.setReadOnly(True)
        self.uninstall_hook_edit.setPlaceholderText("Optional script run before removal")
        hook_browse = QPushButton("Browse…")
        hook_browse.clicked.connect(self._pick_uninstall_hook)
        hook_clear = QPushButton("Clear")
        hook_clear.clicked.connect(self.uninstall_hook_edit.clear)
        hrow = QHBoxLayout()
        hrow.addWidget(self.uninstall_hook_edit)
        hrow.addWidget(hook_browse)
        hrow.addWidget(hook_clear)

        self.remove_paths_list = QListWidget()
        add = QPushButton("Add path…")
        add.clicked.connect(self._add_remove_path)
        rm = QPushButton("Remove")
        rm.clicked.connect(self._remove_remove_path)
        prow = QHBoxLayout()
        prow.addWidget(add)
        prow.addWidget(rm)
        prow.addStretch()

        box = QGroupBox("Uninstall (optional)")
        lay = QVBoxLayout(box)
        lay.addWidget(QLabel("Custom hook, copied to Contents/bin/uninstall and run "
                            "before removal:"))
        lay.addLayout(hrow)
        lay.addWidget(QLabel("Extra absolute paths on the target to delete on uninstall:"))
        lay.addWidget(self.remove_paths_list)
        lay.addLayout(prow)
        return box

    def _pick_uninstall_hook(self) -> None:
        f, _ = QFileDialog.getOpenFileName(self, "Select uninstall hook script")
        if f:
            self.uninstall_hook_edit.setText(f)

    def _add_remove_path(self) -> None:
        text, ok = QInputDialog.getText(
            self, "Add path",
            "Absolute path on the target system to remove on uninstall:")
        if ok and text.strip():
            self.remove_paths_list.addItem(text.strip())

    def _remove_remove_path(self) -> None:
        r = self.remove_paths_list.currentRow()
        if r >= 0:
            self.remove_paths_list.takeItem(r)

    def _output_group(self) -> QGroupBox:
        self.out_edit = QLineEdit()
        self.out_edit.setPlaceholderText("Where to write the .exe bundle")
        browse = QPushButton("Browse…")
        browse.clicked.connect(self._pick_output)
        row = QHBoxLayout()
        row.addWidget(self.out_edit)
        row.addWidget(browse)
        box = QGroupBox("Output directory")
        lay = QVBoxLayout(box)
        lay.addLayout(row)
        return box

    def _action_buttons(self) -> QHBoxLayout:
        load = QPushButton("Load Template")
        load.clicked.connect(self._load_template)
        save = QPushButton("Save Template")
        save.clicked.connect(self._save_template)
        build = QPushButton("Build Bundle")
        build.clicked.connect(self._build_bundle)
        build_inst = QPushButton("Build Bundle + Installer")
        build_inst.clicked.connect(self._build_installer)
        row = QHBoxLayout()
        row.addWidget(load)
        row.addWidget(save)
        row.addStretch()
        row.addWidget(build)
        row.addWidget(build_inst)
        return row

    def _pick_exec(self) -> None:
        f, _ = QFileDialog.getOpenFileName(self, "Select executable")
        if f:
            self.exec_edit.setText(f)

    def _add_deps(self) -> None:
        files, _ = QFileDialog.getOpenFileNames(self, "Select dependency libraries")
        for f in files:
            self.dep_list.addItem(f)

    def _remove_dep(self) -> None:
        r = self.dep_list.currentRow()
        if r >= 0:
            self.dep_list.takeItem(r)

    def _autodetect_deps(self) -> None:
        exe = self.exec_edit.text().strip()
        if not exe or not Path(exe).is_file():
            QMessageBox.warning(self, "Auto-detect", "Select an executable first.")
            return
        found = builder.detect_dependencies(Path(exe))
        if not found:
            QMessageBox.information(
                self, "Auto-detect",
                "No bundleable libraries found (ldd unavailable, or only core "
                "system libraries are linked).")
            return
        existing = {self.dep_list.item(i).text() for i in range(self.dep_list.count())}
        added = 0
        for dep in found:
            if dep not in existing:
                self.dep_list.addItem(dep)
                added += 1
        QMessageBox.information(
            self, "Auto-detect",
            f"Added {added} libraries. Review the list and remove any you expect "
            "to come from the system rather than be bundled.")

    def _pick_icon(self) -> None:
        f, _ = QFileDialog.getOpenFileName(
            self, "Select icon", filter="Images (*.png *.jpg *.jpeg *.svg *.ico)")
        if f:
            self.icon_edit.setText(f)
            self._show_icon_preview(f)

    def _show_icon_preview(self, path: str) -> None:
        pm = QPixmap(path)
        if not pm.isNull():
            self.icon_preview.setPixmap(pm.scaled(
                96, 96, Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation))

    def _pick_output(self) -> None:
        d = QFileDialog.getExistingDirectory(self, "Output directory")
        if d:
            self.out_edit.setText(d)

    def _env_add(self, name: str = "", value: str = "") -> None:
        r = self.env_table.rowCount()
        self.env_table.insertRow(r)
        self.env_table.setItem(r, 0, QTableWidgetItem(name))
        self.env_table.setItem(r, 1, QTableWidgetItem(value))

    def _env_remove(self) -> None:
        r = self.env_table.currentRow()
        if r >= 0:
            self.env_table.removeRow(r)

    def _collect_spec(self) -> dict:
        env = {}
        for r in range(self.env_table.rowCount()):
            n = self.env_table.item(r, 0)
            v = self.env_table.item(r, 1)
            name = (n.text() if n else "").strip()
            if name:
                env[name] = v.text() if v else ""
        sizes = [int(t) for t in self.sizes_edit.text().split(",") if t.strip().isdigit()]
        return {
            "id": self.id_edit.text().strip(),
            "name": self.name_edit.text().strip(),
            "version": self.version_edit.text().strip(),
            "comment": self.comment_edit.text().strip(),
            "categories": self.categories_edit.text().strip() or "Utility",
            "exec_source": self.exec_edit.text().strip(),
            "dependencies": [self.dep_list.item(i).text() for i in range(self.dep_list.count())],
            "icon_source": self.icon_edit.text().strip(),
            "icon_sizes": sizes or builder.DEFAULT_ICON_SIZES,
            "env": env,
            "uninstall_hook_source": self.uninstall_hook_edit.text().strip(),
            "uninstall_remove_paths": [
                self.remove_paths_list.item(i).text()
                for i in range(self.remove_paths_list.count())
            ],
        }

    def _apply_spec(self, spec: dict) -> None:
        self.id_edit.setText(spec.get("id", ""))
        self.name_edit.setText(spec.get("name", ""))
        self.version_edit.setText(spec.get("version", "1.0.0"))
        self.comment_edit.setText(spec.get("comment", ""))
        self.categories_edit.setText(spec.get("categories", "Utility"))
        self.exec_edit.setText(spec.get("exec_source", ""))
        self.dep_list.clear()
        for d in spec.get("dependencies", []):
            self.dep_list.addItem(d)
        self.icon_edit.setText(spec.get("icon_source", ""))
        if spec.get("icon_source"):
            self._show_icon_preview(spec["icon_source"])
        sizes = spec.get("icon_sizes") or builder.DEFAULT_ICON_SIZES
        self.sizes_edit.setText(",".join(str(s) for s in sizes))
        self.env_table.setRowCount(0)
        for name, value in (spec.get("env") or {}).items():
            self._env_add(name, str(value))
        self.uninstall_hook_edit.setText(spec.get("uninstall_hook_source", ""))
        self.remove_paths_list.clear()
        for p in spec.get("uninstall_remove_paths", []):
            self.remove_paths_list.addItem(p)

    def _validate(self, spec: dict) -> str | None:
        if not spec["exec_source"] or not Path(spec["exec_source"]).is_file():
            return "Select a valid executable."
        if not (spec["name"] or spec["id"]):
            return "Set a display name or bundle ID."
        if not self.out_edit.text().strip():
            return "Choose an output directory."
        return None

    def _output_dir(self) -> Path:
        out = Path(self.out_edit.text().strip())
        out.mkdir(parents=True, exist_ok=True)
        return out

    def _build_bundle(self) -> None:
        spec = self._collect_spec()
        err = self._validate(spec)
        if err:
            QMessageBox.warning(self, "Cannot build", err)
            return
        try:
            bundle = builder.build_bundle(spec, self._output_dir())
        except Exception as e:
            QMessageBox.critical(self, "Build failed", str(e))
            return
        QMessageBox.information(self, "Built", f"Bundle created:\n{bundle}")

    def _build_installer(self) -> None:
        spec = self._collect_spec()
        err = self._validate(spec)
        if err:
            QMessageBox.warning(self, "Cannot build", err)
            return
        try:
            out = self._output_dir()
            bundle = builder.build_bundle(spec, out)
            installer = builder.build_installer(spec, bundle, out)
        except Exception as e:
            QMessageBox.critical(self, "Build failed", str(e))
            return
        QMessageBox.information(self, "Built", f"Bundle:\n{bundle}\n\nInstaller:\n{installer}")

    def _save_template(self) -> None:
        f, _ = QFileDialog.getSaveFileName(self, "Save template", filter="JSON (*.json)")
        if not f:
            return
        if not f.endswith(".json"):
            f += ".json"
        builder.save_template(self._collect_spec(), Path(f))
        QMessageBox.information(self, "Saved", f"Template saved:\n{f}")

    def _load_template(self) -> None:
        f, _ = QFileDialog.getOpenFileName(self, "Load template", filter="JSON (*.json)")
        if not f:
            return
        try:
            spec = builder.load_template(Path(f))
        except Exception as e:
            QMessageBox.critical(self, "Load failed", str(e))
            return
        self._apply_spec(spec)
