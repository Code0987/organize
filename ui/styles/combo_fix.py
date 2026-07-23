"""Workarounds for QComboBox popup not closing after selection.

Custom application stylesheets (especially under Wayland / WSLg) can leave
the combo popup stuck open after a click. We force a non-native list view
and explicitly hide the popup when an item is chosen.
"""

from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication, QComboBox, QListView, QWidget


_PATCH_FLAG = "_organize_combo_popup_fixed"


def configure_combobox(combo: QComboBox) -> QComboBox:
    """Make *combo* reliably close its dropdown after a selection."""
    if bool(combo.property(_PATCH_FLAG)):
        return combo

    view = QListView(combo)
    view.setUniformItemSizes(True)
    view.setMouseTracking(True)
    # Keep the popup opaque so it does not fight compositor / stylesheet quirks.
    view.setAutoFillBackground(True)
    combo.setView(view)
    combo.setMaxVisibleItems(16)

    def _close_popup(*_args: object) -> None:
        # Defer until after Qt finishes handling the click/activation.
        QTimer.singleShot(0, combo.hidePopup)

    combo.activated.connect(_close_popup)
    combo.textActivated.connect(_close_popup)
    combo.setProperty(_PATCH_FLAG, True)
    return combo


def polish_comboboxes(root: Optional[QWidget] = None) -> None:
    """Patch every :class:`QComboBox` under *root* (or the whole application)."""
    widgets: list[QWidget]
    if root is not None:
        widgets = [root, *root.findChildren(QComboBox)]
    else:
        app = QApplication.instance()
        if app is None:
            return
        widgets = list(app.allWidgets())

    for widget in widgets:
        if isinstance(widget, QComboBox):
            configure_combobox(widget)
