"""Combo box that does not change value when the rule editor is scrolled."""

from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QWheelEvent
from PyQt6.QtWidgets import QComboBox, QWidget


class ScrollComboBox(QComboBox):
    """QComboBox that ignores the mouse wheel unless its popup is open.

    Combo boxes inside a QScrollArea steal wheel events and cycle their
    current item. That rewrites the rule as the user tries to scroll.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        # WheelFocus would give this widget focus just by scrolling over it.
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def wheelEvent(self, event: QWheelEvent) -> None:  # noqa: N802
        if self.view() is not None and self.view().isVisible():
            super().wheelEvent(event)
            return
        event.ignore()
