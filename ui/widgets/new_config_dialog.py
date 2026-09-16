"""Dialog that lets the user start from a built-in preset."""

from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QResizeEvent, QShowEvent
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
)

from ui.models.preset import Preset
from ui.models.preset_library import PresetLibrary
from ui.widgets.preset_row import PresetRow


class NewConfigDialog(QDialog):
    """Pick a starter template for a new organize config."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("New config")
        self.resize(560, 520)
        self._library = PresetLibrary()
        self.preset: Optional[Preset] = self._library.default()

        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        heading = QLabel("Start from a preset:")
        heading.setStyleSheet("background: transparent;")
        layout.addWidget(heading)

        self.list = QListWidget()
        self.list.setObjectName("presetList")
        self.list.setSpacing(6)
        self.list.setUniformItemSizes(False)
        self.list.setWordWrap(True)
        self.list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.list.setStyleSheet(
            """
            QListWidget#presetList::item {
                padding: 0px;
                margin: 0px;
            }
            """
        )
        for preset in self._library.all():
            row = PresetRow(preset)
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, preset.id)
            item.setSizeHint(row.sizeHint())
            self.list.addItem(item)
            self.list.setItemWidget(item, row)
        self.list.setCurrentRow(0)
        self.list.currentRowChanged.connect(self._pick)
        layout.addWidget(self.list, 1)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def showEvent(self, event: QShowEvent) -> None:  # noqa: N802
        super().showEvent(event)
        self._sync_row_sizes()

    def resizeEvent(self, event: QResizeEvent) -> None:  # noqa: N802
        super().resizeEvent(event)
        self._sync_row_sizes()

    def _sync_row_sizes(self) -> None:
        """Give each custom row the viewport width so descriptions wrap cleanly."""
        width = max(self.list.viewport().width() - 8, 200)
        for index in range(self.list.count()):
            item = self.list.item(index)
            widget = self.list.itemWidget(item)
            if item is None or widget is None:
                continue
            widget.setFixedWidth(width)
            hint = widget.sizeHint()
            item.setSizeHint(QSize(width, max(hint.height(), 56)))

    def _pick(self, row: int) -> None:
        presets = self._library.all()
        if 0 <= row < len(presets):
            self.preset = presets[row]
