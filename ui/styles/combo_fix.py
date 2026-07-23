"""Reliable QComboBox that dismisses its popup after a choice.

Under Wayland/WSLg, styled QComboBox popups often stay open after a click.
We close them explicitly — but *without* destroying the popup container, which
left the list empty on the second open.
"""

from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import QEvent, QObject, Qt, QTimer
from PyQt6.QtWidgets import QApplication, QComboBox, QListView, QWidget


_PATCH_FLAG = "_organize_combo_popup_fixed"


class _PopupCloseFilter(QObject):
    """Select the clicked row and dismiss the popup."""

    def __init__(self, combo: QComboBox) -> None:
        super().__init__(combo)
        self._combo = combo
        self._closing = False

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:  # noqa: N802
        if event.type() != QEvent.Type.MouseButtonRelease:
            return super().eventFilter(obj, event)

        view = self._combo.view()
        if view is None or obj is not view.viewport():
            return super().eventFilter(obj, event)

        try:
            if event.button() != Qt.MouseButton.LeftButton:  # type: ignore[attr-defined]
                return super().eventFilter(obj, event)
            pos = event.position().toPoint()  # type: ignore[attr-defined]
        except Exception:
            return super().eventFilter(obj, event)

        index = view.indexAt(pos)
        if not index.isValid():
            return super().eventFilter(obj, event)

        if self._closing:
            return True
        self._closing = True
        try:
            row = index.row()
            if self._combo.currentIndex() != row:
                self._combo.setCurrentIndex(row)
            # Soft-dismiss only — never destroy the popup host widget.
            soft_close_combo_popup(self._combo)
            self._combo.activated.emit(row)
            self._combo.textActivated.emit(self._combo.itemText(row))
            QTimer.singleShot(0, lambda: soft_close_combo_popup(self._combo))
        finally:
            # Allow future opens/selections.
            QTimer.singleShot(50, lambda: setattr(self, "_closing", False))
        return True


def soft_close_combo_popup(combo: QComboBox) -> None:
    """Hide the popup without destroying its view/container.

    Calling ``close()`` on Qt's internal popup frame was wiping the item list
    for subsequent opens. Stick to hidePopup + hide on the transient window.
    """
    try:
        QComboBox.hidePopup(combo)
    except Exception:
        pass

    view = combo.view()
    if view is None:
        return

    # Hide the transient popup window if Qt placed the view in one — do not close().
    try:
        top = view.window()
        if top is not None and top is not combo and top is not combo.window():
            top.hide()
    except Exception:
        pass


def _ensure_list_view(combo: QComboBox) -> QListView:
    """Return a healthy list view for *combo*, recreating it if needed."""
    view = combo.view()
    # sip/cpp object may be deleted after a hard close; treat as missing.
    try:
        alive = view is not None and view.model() is not None
        if alive and isinstance(view, QListView):
            # Touch a property to detect deleted C++ wrappers.
            _ = view.isVisible()
            return view  # type: ignore[return-value]
    except RuntimeError:
        alive = False

    view = QListView(combo)
    view.setUniformItemSizes(True)
    view.setMouseTracking(True)
    view.setAutoFillBackground(True)
    view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    view.setSelectionBehavior(QListView.SelectionBehavior.SelectRows)
    view.setSelectionMode(QListView.SelectionMode.SingleSelection)
    combo.setView(view)
    return view


def configure_combobox(combo: QComboBox) -> QComboBox:
    """Harden *combo* so its dropdown closes after a selection and reopens with items."""
    if bool(combo.property(_PATCH_FLAG)):
        # Still re-bind the view in case a previous close destroyed it.
        _ensure_list_view(combo)
        return combo

    view = _ensure_list_view(combo)
    combo.setMaxVisibleItems(16)
    combo.setEditable(False)

    def _on_activated(*_args: object) -> None:
        soft_close_combo_popup(combo)
        QTimer.singleShot(0, lambda: soft_close_combo_popup(combo))

    combo.activated.connect(_on_activated)
    combo.textActivated.connect(_on_activated)

    popup_filter = _PopupCloseFilter(combo)
    view.viewport().installEventFilter(popup_filter)
    combo.setProperty("_organize_combo_filter", popup_filter)
    combo.setProperty(_PATCH_FLAG, True)
    return combo


class ClosingComboBox(QComboBox):
    """Drop-in QComboBox that dismisses after a selection and keeps items intact."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        configure_combobox(self)

    def hidePopup(self) -> None:  # noqa: N802
        soft_close_combo_popup(self)

    def showPopup(self) -> None:  # noqa: N802
        # Recreate the list view if a previous dismiss left it unusable.
        view = _ensure_list_view(self)
        filt = self.property("_organize_combo_filter")
        if isinstance(filt, QObject):
            try:
                view.viewport().installEventFilter(filt)
            except RuntimeError:
                # Viewport was recreated with the view.
                popup_filter = _PopupCloseFilter(self)
                view.viewport().installEventFilter(popup_filter)
                self.setProperty("_organize_combo_filter", popup_filter)

        # Make sure the model still has rows (paranoia for empty second open).
        model = self.model()
        if model is not None and model.rowCount() == 0 and self.count() > 0:
            # Force model refresh from combo items.
            self.setModel(self.model())

        super().showPopup()


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
