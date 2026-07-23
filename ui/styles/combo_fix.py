"""Dropdown controls that work reliably under Wayland / WSLg.

Native :class:`~PyQt6.QtWidgets.QComboBox` popups frequently misbehave when an
application stylesheet is set (stuck open, empty second open, or dead clicks).

This module provides :class:`MenuSelect` — a QComboBox-like control built on
:class:`~PyQt6.QtWidgets.QToolButton` + :class:`~PyQt6.QtWidgets.QMenu`, which
closes and reopens correctly on every platform we care about.

For call-site compatibility the old names ``ClosingComboBox`` and
``configure_combobox`` still exist as aliases.
"""

from __future__ import annotations

from typing import Any, Iterable, List, Optional, Sequence, Tuple

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QSizePolicy,
    QToolButton,
    QMenu,
    QWidget,
)


class MenuSelect(QWidget):
    """QComboBox-compatible dropdown implemented with a button menu.

    Supported API (subset used by this app)::

        addItem(text, userData=None)
        addItems(texts)
        count() / itemText(i) / currentText()
        currentIndex() / setCurrentIndex(i)
        currentData() / findData(value) / findText(text)
        currentIndexChanged(int)
        activated(int)
    """

    currentIndexChanged = pyqtSignal(int)
    activated = pyqtSignal(int)
    textActivated = pyqtSignal(str)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._items: List[Tuple[str, Any]] = []
        self._index: int = -1
        self._block = False

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._button = QToolButton(self)
        self._button.setObjectName("MenuSelectButton")
        self._button.setToolButtonStyle(
            self._button.toolButtonStyle()  # keep default text-only feel
        )
        from PyQt6.QtCore import Qt

        self._button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        self._button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self._button.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        self._button.setAutoRaise(False)
        self._menu = QMenu(self._button)
        self._button.setMenu(self._menu)
        layout.addWidget(self._button)

        self._sync_button_label()

    # ----- QComboBox-like API -------------------------------------------

    def addItem(self, text: str, userData: Any = None) -> None:  # noqa: N802
        self._items.append((str(text), userData))
        self._rebuild_menu()
        if self._index < 0:
            self.setCurrentIndex(0)

    def addItems(self, texts: Iterable[str]) -> None:  # noqa: N802
        for text in texts:
            self._items.append((str(text), None))
        self._rebuild_menu()
        if self._index < 0 and self._items:
            self.setCurrentIndex(0)

    def count(self) -> int:
        return len(self._items)

    def itemText(self, index: int) -> str:  # noqa: N802
        if 0 <= index < len(self._items):
            return self._items[index][0]
        return ""

    def currentIndex(self) -> int:  # noqa: N802
        return self._index

    def currentText(self) -> str:  # noqa: N802
        if 0 <= self._index < len(self._items):
            return self._items[self._index][0]
        return ""

    def currentData(self) -> Any:  # noqa: N802
        if 0 <= self._index < len(self._items):
            return self._items[self._index][1]
        return None

    def setCurrentIndex(self, index: int) -> None:  # noqa: N802
        if index < 0 or index >= len(self._items):
            return
        if index == self._index:
            self._sync_button_label()
            return
        self._index = index
        self._sync_button_label()
        if not self._block:
            self.currentIndexChanged.emit(index)

    def findData(self, value: Any) -> int:  # noqa: N802
        for i, (_text, data) in enumerate(self._items):
            if data == value:
                return i
        return -1

    def findText(self, text: str) -> int:  # noqa: N802
        for i, (item_text, _data) in enumerate(self._items):
            if item_text == text:
                return i
        return -1

    def clear(self) -> None:
        self._items.clear()
        self._index = -1
        self._rebuild_menu()
        self._sync_button_label()

    # ----- internals ----------------------------------------------------

    def _rebuild_menu(self) -> None:
        self._menu.clear()
        for i, (text, _data) in enumerate(self._items):
            action = self._menu.addAction(text)
            # Default-arg bind index so the lambda does not close over the loop var.
            action.triggered.connect(lambda _checked=False, idx=i: self._on_pick(idx))

    def _on_pick(self, index: int) -> None:
        self.setCurrentIndex(index)
        self.activated.emit(index)
        self.textActivated.emit(self.itemText(index))
        # QMenu closes itself after triggered — that is the whole point.

    def _sync_button_label(self) -> None:
        text = self.currentText() or "Select…"
        # Trailing arrow hint (menu is InstantPopup).
        self._button.setText(f"{text}  ▾")

    def blockSignals(self, block: bool) -> bool:  # noqa: N802
        """Match QObject.blockSignals and also suppress our index emissions."""
        prev = self._block
        self._block = block
        super().blockSignals(block)
        return prev


# Back-compat aliases used across the codebase / older tests.
ClosingComboBox = MenuSelect


def configure_combobox(combo: QWidget) -> QWidget:
    """No-op for MenuSelect; kept so polish hooks stay safe."""
    return combo


def polish_comboboxes(root: Optional[QWidget] = None) -> None:
    """No-op: MenuSelect does not need runtime patching."""
    return


def soft_close_combo_popup(combo: QWidget) -> None:
    """No-op compatibility helper for tests."""
    return
