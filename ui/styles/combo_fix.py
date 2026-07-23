"""Reliable QComboBox that always dismisses its popup after a choice.

Application stylesheets + Wayland/WSLg frequently leave Qt's combo popup
stuck open after an item click. This module provides:

* :class:`ClosingComboBox` — drop-in replacement used by the UI
* :func:`configure_combobox` — harden an existing QComboBox
* :func:`polish_comboboxes` — patch every combo currently alive
"""

from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import QEvent, QObject, Qt, QTimer
from PyQt6.QtWidgets import QApplication, QComboBox, QListView, QWidget


_PATCH_FLAG = "_organize_combo_popup_fixed"


class _PopupCloseFilter(QObject):
    """Close the owning combo when the popup list is clicked."""

    def __init__(self, combo: QComboBox) -> None:
        super().__init__(combo)
        self._combo = combo

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:  # noqa: N802
        et = event.type()
        if et not in (
            QEvent.Type.MouseButtonRelease,
            QEvent.Type.MouseButtonDblClick,
        ):
            return super().eventFilter(obj, event)

        view = self._combo.view()
        if view is None or obj is not view.viewport():
            return super().eventFilter(obj, event)

        try:
            button = event.button()  # type: ignore[attr-defined]
            pos = event.position().toPoint()  # type: ignore[attr-defined]
        except Exception:
            return super().eventFilter(obj, event)

        if button != Qt.MouseButton.LeftButton:
            return super().eventFilter(obj, event)

        index = view.indexAt(pos)
        if not index.isValid():
            return super().eventFilter(obj, event)

        row = index.row()
        # Apply selection, then tear the popup down. Consume the event so Qt
        # does not re-open / re-handle the click in a broken way.
        if self._combo.currentIndex() != row:
            self._combo.setCurrentIndex(row)
        force_close_combo_popup(self._combo)
        self._combo.activated.emit(row)
        self._combo.textActivated.emit(self._combo.itemText(row))
        # Second pass for compositors that re-show the popup frame.
        QTimer.singleShot(0, lambda: force_close_combo_popup(self._combo))
        QTimer.singleShot(40, lambda: force_close_combo_popup(self._combo))
        return True


def force_close_combo_popup(combo: QComboBox) -> None:
    """Hide the popup and any container windows hosting the list.

    Always call :meth:`QComboBox.hidePopup` via the base class so subclasses
    that override ``hidePopup`` cannot recurse into this helper.
    """
    try:
        QComboBox.hidePopup(combo)
    except Exception:
        pass

    view = combo.view()
    if view is None:
        return

    try:
        view.hide()
    except Exception:
        pass

    # Walk parents: the list view lives inside a private Qt container frame.
    parent: Optional[QWidget] = view.parentWidget()
    depth = 0
    while parent is not None and depth < 8:
        if parent is combo or parent is combo.window():
            break
        try:
            parent.hide()
            if parent.isWindow():
                parent.close()
        except Exception:
            pass
        parent = parent.parentWidget()
        depth += 1

    try:
        top = view.window()
        if top is not None and top is not combo.window() and top is not combo:
            top.hide()
            top.close()
    except Exception:
        pass


def configure_combobox(combo: QComboBox) -> QComboBox:
    """Harden *combo* so its dropdown always closes after a selection."""
    if bool(combo.property(_PATCH_FLAG)):
        return combo

    view = QListView(combo)
    view.setUniformItemSizes(True)
    view.setMouseTracking(True)
    view.setAutoFillBackground(True)
    view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    view.setSelectionBehavior(QListView.SelectionBehavior.SelectRows)
    view.setSelectionMode(QListView.SelectionMode.SingleSelection)
    combo.setView(view)
    combo.setMaxVisibleItems(16)
    combo.setEditable(False)

    def _on_activated(*_args: object) -> None:
        force_close_combo_popup(combo)
        QTimer.singleShot(0, lambda: force_close_combo_popup(combo))
        QTimer.singleShot(40, lambda: force_close_combo_popup(combo))

    combo.activated.connect(_on_activated)
    combo.textActivated.connect(_on_activated)

    popup_filter = _PopupCloseFilter(combo)
    view.viewport().installEventFilter(popup_filter)
    # Keep a Python reference so the filter is not garbage-collected.
    combo.setProperty("_organize_combo_filter", popup_filter)

    combo.setProperty(_PATCH_FLAG, True)
    return combo


class ClosingComboBox(QComboBox):
    """Drop-in QComboBox that always dismisses after a selection."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        configure_combobox(self)

    def hidePopup(self) -> None:  # noqa: N802
        # Do not call self.hidePopup recursion; force_close uses the base method.
        force_close_combo_popup(self)

    def showPopup(self) -> None:  # noqa: N802
        super().showPopup()
        view = self.view()
        if view is None:
            return
        filt = self.property("_organize_combo_filter")
        if isinstance(filt, QObject):
            view.viewport().installEventFilter(filt)


def polish_comboboxes(root: Optional[QWidget] = None) -> None:
    """Patch every :class:`QComboBox` under *root* (or the whole application)."""
    if root is not None:
        candidates = [root, *root.findChildren(QComboBox)]
    else:
        app = QApplication.instance()
        if app is None:
            return
        candidates = list(app.allWidgets())

    for widget in candidates:
        if isinstance(widget, QComboBox):
            configure_combobox(widget)
