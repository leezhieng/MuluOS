"""Start Menu settings panel — embeds the shared menu editor widget."""
from __future__ import annotations

from PyQt6.QtWidgets import QWidget

from muluos_menu_editor.widget import MenuEditorWidget

from ..panel import Panel


class StartMenuPanel(Panel):
    def title(self) -> str:
        return "Start Menu"

    def icon_name(self) -> str:
        return "start-here-kde"

    def widget(self) -> QWidget:
        return MenuEditorWidget()
