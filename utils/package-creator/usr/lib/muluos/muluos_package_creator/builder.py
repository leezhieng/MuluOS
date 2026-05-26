"""Build MuluOS .exe bundles and installers from a spec dict.

A spec is the in-memory form of the saved JSON template:

    {
      "id": "com.example.myapp",
      "name": "My App",
      "version": "1.0.0",
      "comment": "Does a thing",
      "categories": "Utility",
      "exec_source": "/abs/path/to/binary",
      "dependencies": ["/abs/path/libfoo.so", ...],
      "icon_source": "/abs/path/icon.png",
      "icon_sizes": [16, 32, 48, 64, 128, 256, 512],
      "env": {"KEY": "value"}
    }

Bundle layout produced:

    <Name>.exe/
      Info.json
      Contents/bin/<exec>     the executable (LD_LIBRARY_PATH includes this dir)
      Contents/lib/<deps>     bundled shared libraries
      Resources/icons/<n>.png generated icon sizes
"""
from __future__ import annotations
import json
import re
import shutil
import stat
import subprocess
from pathlib import Path

DEFAULT_ICON_SIZES = [16, 32, 48, 64, 128, 256, 512]
EXEC_SUBDIR = "Contents/bin"
LIB_SUBDIR = "Contents/lib"
ICON_SUBDIR = "Resources/icons"


def build_bundle(spec: dict, output_dir: Path) -> Path:
    name = spec.get("name") or spec.get("id") or "App"
    bundle = output_dir / f"{_safe_name(name)}.exe"
    if bundle.exists():
        shutil.rmtree(bundle)
    (bundle / EXEC_SUBDIR).mkdir(parents=True)
    (bundle / LIB_SUBDIR).mkdir(parents=True)
    (bundle / ICON_SUBDIR).mkdir(parents=True)

    exec_source = Path(spec["exec_source"])
    exec_name = exec_source.name
    exec_dst = bundle / EXEC_SUBDIR / exec_name
    shutil.copy2(exec_source, exec_dst)
    _make_executable(exec_dst)

    for dep in spec.get("dependencies", []):
        dep_path = Path(dep)
        if dep_path.is_file():
            shutil.copy2(dep_path, bundle / LIB_SUBDIR / dep_path.name)

    icon_rel = ""
    icon_source = spec.get("icon_source")
    sizes = spec.get("icon_sizes") or DEFAULT_ICON_SIZES
    if icon_source and Path(icon_source).is_file():
        generate_icons(Path(icon_source), bundle / ICON_SUBDIR, sizes)
        icon_rel = f"{ICON_SUBDIR}/{max(sizes)}.png"

    info = {
        "id": spec.get("id") or _safe_name(name).lower(),
        "name": name,
        "version": spec.get("version", "1.0.0"),
        "comment": spec.get("comment", ""),
        "categories": spec.get("categories", "Utility"),
        "exec": f"{EXEC_SUBDIR}/{exec_name}",
    }
    if icon_rel:
        info["icon"] = icon_rel
    env = spec.get("env")
    if isinstance(env, dict) and env:
        info["env"] = env

    uninstall: dict = {}
    hook_src = spec.get("uninstall_hook_source")
    if hook_src and Path(hook_src).is_file():
        hook_dst = bundle / EXEC_SUBDIR / "uninstall"
        shutil.copy2(hook_src, hook_dst)
        _make_executable(hook_dst)
        uninstall["exec"] = f"{EXEC_SUBDIR}/uninstall"
    remove_paths = [p for p in spec.get("uninstall_remove_paths", []) if p.strip()]
    if remove_paths:
        uninstall["remove_paths"] = remove_paths
    if uninstall:
        info["uninstall"] = uninstall

    (bundle / "Info.json").write_text(json.dumps(info, indent=2) + "\n", encoding="utf-8")
    return bundle


def generate_icons(source: Path, icons_dir: Path, sizes: list[int]) -> None:
    icons_dir.mkdir(parents=True, exist_ok=True)
    try:
        from PIL import Image
    except ImportError:
        # No Pillow: keep the source as the largest size so the bundle still
        # has a usable icon; smaller sizes are simply absent.
        shutil.copy2(source, icons_dir / f"{max(sizes)}.png")
        return
    with Image.open(source) as im:
        im = im.convert("RGBA")
        for size in sizes:
            im.resize((size, size), Image.LANCZOS).save(icons_dir / f"{size}.png", "PNG")


# Loader + core libc family; these must come from the host, never be bundled.
_CORE_LIB_PREFIXES = (
    "ld-linux", "ld-musl", "libc.", "libm.", "libdl.",
    "libpthread.", "librt.", "libresolv.",
)
_LDD_PATH = re.compile(r"=>\s*(/\S+)")


def detect_dependencies(exec_path: Path) -> list[str]:
    """Resolve shared-library dependencies via ldd, excluding the dynamic
    loader and core libc family. Returns absolute paths; empty if ldd is
    unavailable (e.g. running on a non-Linux host)."""
    try:
        out = subprocess.run(
            ["ldd", str(exec_path)],
            capture_output=True, text=True, timeout=20,
        ).stdout
    except (OSError, subprocess.SubprocessError):
        return []
    deps: set[str] = set()
    for line in out.splitlines():
        m = _LDD_PATH.search(line)
        if not m:
            continue
        path = m.group(1)
        if any(Path(path).name.startswith(p) for p in _CORE_LIB_PREFIXES):
            continue
        if Path(path).is_file():
            deps.add(path)
    return sorted(deps)


def build_installer(spec: dict, app_bundle: Path, output_dir: Path) -> Path:
    name = spec.get("name") or "App"
    installer = output_dir / f"{_safe_name(name)} Installer.exe"
    if installer.exists():
        shutil.rmtree(installer)
    (installer / "Contents" / "bin").mkdir(parents=True)
    (installer / "payload").mkdir(parents=True)
    (installer / ICON_SUBDIR).mkdir(parents=True)

    shutil.copytree(app_bundle, installer / "payload" / app_bundle.name)

    app_icons = app_bundle / ICON_SUBDIR
    if app_icons.is_dir():
        shutil.copytree(app_icons, installer / ICON_SUBDIR, dirs_exist_ok=True)

    install_script = installer / "Contents" / "bin" / "install"
    install_script.write_text(_INSTALL_SCRIPT, encoding="utf-8")
    _make_executable(install_script)

    sizes = spec.get("icon_sizes") or DEFAULT_ICON_SIZES
    info = {
        "id": (spec.get("id") or _safe_name(name).lower()) + ".installer",
        "name": f"Install {name}",
        "version": spec.get("version", "1.0.0"),
        "comment": f"Installer for {name}",
        "categories": "System",
        "exec": "Contents/bin/install",
        "icon": f"{ICON_SUBDIR}/{max(sizes)}.png",
    }
    (installer / "Info.json").write_text(json.dumps(info, indent=2) + "\n", encoding="utf-8")
    return installer


def save_template(spec: dict, path: Path) -> None:
    path.write_text(json.dumps(spec, indent=2) + "\n", encoding="utf-8")


def load_template(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _safe_name(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9._ -]", "_", name).strip() or "App"


def _make_executable(p: Path) -> None:
    p.chmod(p.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


# Embedded into every installer bundle as Contents/bin/install. Launched by
# launch-bundle, it presents a Windows-style step wizard, then copies the
# payload bundle to the chosen location and registers it via muluos-bundle
# (under pkexec for the needed root privileges).
_INSTALL_SCRIPT = '''#!/usr/bin/env python3
"""MuluOS app installer wizard (embedded in an installer .exe bundle)."""
import json
import os
import sys
from pathlib import Path

from PyQt6.QtCore import QProcess
from PyQt6.QtWidgets import (
    QApplication, QFileDialog, QHBoxLayout, QLabel, QLineEdit, QMessageBox,
    QPlainTextEdit, QPushButton, QVBoxLayout, QWizard, QWizardPage,
)

BUNDLE = Path(os.environ.get("MULUOS_BUNDLE", "."))
PAYLOAD = BUNDLE / "payload"
DEFAULT_ROOT = "/opt/muluos/apps"


def find_app():
    if PAYLOAD.is_dir():
        for p in sorted(PAYLOAD.iterdir()):
            if p.name.endswith(".exe") and (p / "Info.json").is_file():
                return p
    return None


def meta_of(app):
    try:
        return json.loads((app / "Info.json").read_text(encoding="utf-8"))
    except Exception:
        return {}


class WelcomePage(QWizardPage):
    def __init__(self, meta):
        super().__init__()
        name = meta.get("name", "Application")
        self.setTitle(f"Welcome to {name} Setup")
        v = QVBoxLayout(self)
        v.addWidget(QLabel(
            f"This wizard will install {name} {meta.get('version', '')} "
            "on your system."))
        if meta.get("comment"):
            v.addWidget(QLabel(meta["comment"]))
        v.addWidget(QLabel("Click Next to continue."))


class LocationPage(QWizardPage):
    def __init__(self, app_name):
        super().__init__()
        self.setTitle("Choose Install Location")
        self.edit = QLineEdit(DEFAULT_ROOT)
        browse = QPushButton("Browse…")
        browse.clicked.connect(self._browse)
        row = QHBoxLayout()
        row.addWidget(self.edit)
        row.addWidget(browse)
        v = QVBoxLayout(self)
        v.addWidget(QLabel(f"{app_name} will be installed into a subfolder of:"))
        v.addLayout(row)
        self.registerField("install_root", self.edit)

    def _browse(self):
        d = QFileDialog.getExistingDirectory(self, "Install location", self.edit.text())
        if d:
            self.edit.setText(d)


class InstallPage(QWizardPage):
    def __init__(self, app_path):
        super().__init__()
        self.app_path = app_path
        self.setTitle("Installing")
        self._done = False
        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        v = QVBoxLayout(self)
        v.addWidget(self.log)

    def isComplete(self):
        return self._done

    def initializePage(self):
        root = self.field("install_root") or DEFAULT_ROOT
        dest = f"{root}/{self.app_path.name}"
        cmd = (f"mkdir -p {root} && rm -rf '{dest}' && "
               f"cp -r '{self.app_path}' '{dest}' && "
               f"muluos-bundle install '{dest}'")
        self.log.appendPlainText(f"Installing to {dest} …")
        self.proc = QProcess(self)
        self.proc.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self.proc.readyReadStandardOutput.connect(self._read)
        self.proc.finished.connect(self._finished)
        self.proc.start("pkexec", ["sh", "-c", cmd])

    def _read(self):
        data = bytes(self.proc.readAllStandardOutput()).decode(errors="replace")
        if data.strip():
            self.log.appendPlainText(data.rstrip())

    def _finished(self, code, _status):
        ok = code == 0
        self._done = True
        self.log.appendPlainText("Done." if ok else f"Failed (exit {code}).")
        self.wizard().setProperty("install_ok", ok)
        self.completeChanged.emit()


class FinishPage(QWizardPage):
    def __init__(self, meta):
        super().__init__()
        self.meta = meta
        self.setTitle("Setup Complete")
        self.label = QLabel()
        v = QVBoxLayout(self)
        v.addWidget(self.label)

    def initializePage(self):
        ok = bool(self.wizard().property("install_ok"))
        name = self.meta.get("name", "The application")
        self.label.setText(
            f"{name} was installed successfully." if ok else
            f"{name} could not be installed. See the log on the previous page.")


def main():
    app = QApplication(sys.argv)
    target = find_app()
    if target is None:
        QMessageBox.critical(None, "Installer", "No app bundle found in payload.")
        return 1
    meta = meta_of(target)
    wiz = QWizard()
    wiz.setWindowTitle(f"{meta.get('name', 'MuluOS')} Installer")
    wiz.addPage(WelcomePage(meta))
    wiz.addPage(LocationPage(meta.get("name", target.stem)))
    wiz.addPage(InstallPage(target))
    wiz.addPage(FinishPage(meta))
    wiz.resize(560, 440)
    wiz.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
'''
