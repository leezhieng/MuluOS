"""Base class for MuluOS Settings panels."""
from __future__ import annotations

from PyQt6.QtWidgets import QWidget


class Panel:
    """Subclass and override title()/icon_name()/widget()."""

    def title(self) -> str:
        raise NotImplementedError

    def icon_name(self) -> str:
        return "preferences-system"

    def widget(self) -> QWidget:
        raise NotImplementedError
