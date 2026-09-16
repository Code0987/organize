"""Spin box that does not change value when the rule editor is scrolled."""

from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QWheelEvent
from PyQt6.QtWidgets import QSpinBox, QWidget


class ScrollSpinBox(QSpinBox):
    """QSpinBox that ignores the mouse wheel unless it already has focus."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def wheelEvent(self, event: QWheelEvent) -> None:  # noqa: N802
        if self.hasFocus():
            super().wheelEvent(event)
            return
        event.ignore()
