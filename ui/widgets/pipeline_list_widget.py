"""List widget for filters or actions with add/edit/remove/reorder."""

from __future__ import annotations

from typing import List, Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ui.models.pipeline_item import ItemKind, PipelineItem
from ui.widgets.item_editor_dialog import ItemEditorDialog


class PipelineListWidget(QWidget):
    """Interactive list of :class:`PipelineItem` entries."""

    changed = pyqtSignal()

    def __init__(self, kind: ItemKind, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.kind = kind
        self._items: List[PipelineItem] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        header = QHBoxLayout()
        label = QLabel("Filters" if kind == "filter" else "Actions")
        label.setObjectName("SectionTitle")
        header.addWidget(label)
        header.addStretch(1)

        self.add_btn = QPushButton("+ Add")
        self.add_btn.setObjectName("AccentButton")
        self.add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        header.addWidget(self.add_btn)
        layout.addLayout(header)

        hint = QLabel(
            "Match which files this rule applies to"
            if kind == "filter"
            else "What to do with matching files"
        )
        hint.setObjectName("HintLabel")
        layout.addWidget(hint)

        self.list_widget = QListWidget()
        self.list_widget.setMinimumHeight(110)
        self.list_widget.setMaximumHeight(180)
        layout.addWidget(self.list_widget)

        tools = QHBoxLayout()
        tools.setSpacing(4)
        self.edit_btn = self._ghost("Edit")
        self.remove_btn = self._ghost("Remove")
        self.up_btn = self._ghost("↑")
        self.down_btn = self._ghost("↓")
        for btn in (self.edit_btn, self.remove_btn, self.up_btn, self.down_btn):
            tools.addWidget(btn)
        tools.addStretch(1)
        layout.addLayout(tools)

        self.add_btn.clicked.connect(self._add)
        self.edit_btn.clicked.connect(self._edit)
        self.remove_btn.clicked.connect(self._remove)
        self.up_btn.clicked.connect(lambda: self._move(-1))
        self.down_btn.clicked.connect(lambda: self._move(1))
        self.list_widget.itemDoubleClicked.connect(lambda _: self._edit())

    @staticmethod
    def _ghost(text: str) -> QPushButton:
        btn = QPushButton(text)
        btn.setObjectName("GhostButton")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        return btn

    def set_items(self, items: List[PipelineItem]) -> None:
        """Replace the list with copies of *items*."""
        self._items = [item.clone() for item in items]
        self._refresh()

    def items(self) -> List[PipelineItem]:
        """Return clones of the current items."""
        return [item.clone() for item in self._items]

    def _refresh(self) -> None:
        self.list_widget.clear()
        if not self._items:
            self.list_widget.addItem("No items yet — click + Add")
            item = self.list_widget.item(0)
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            return
        for item in self._items:
            self.list_widget.addItem(item.display_label())

    def _add(self) -> None:
        dialog = ItemEditorDialog(self.kind, parent=self)
        if dialog.exec():
            self._items.append(dialog.result_item())
            self._refresh()
            self.changed.emit()

    def _edit(self) -> None:
        row = self.list_widget.currentRow()
        if row < 0 or not self._items:
            return
        if row >= len(self._items):
            return
        dialog = ItemEditorDialog(self.kind, item=self._items[row], parent=self)
        if dialog.exec():
            self._items[row] = dialog.result_item()
            self._refresh()
            self.list_widget.setCurrentRow(row)
            self.changed.emit()

    def _remove(self) -> None:
        row = self.list_widget.currentRow()
        if row < 0 or not self._items or row >= len(self._items):
            return
        del self._items[row]
        self._refresh()
        self.changed.emit()

    def _move(self, delta: int) -> None:
        row = self.list_widget.currentRow()
        if row < 0 or not self._items:
            return
        new_row = row + delta
        if new_row < 0 or new_row >= len(self._items):
            return
        self._items[row], self._items[new_row] = self._items[new_row], self._items[row]
        self._refresh()
        self.list_widget.setCurrentRow(new_row)
        self.changed.emit()
