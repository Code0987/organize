"""Editable list of filesystem locations for a rule."""

from __future__ import annotations

from typing import List, Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QListWidget,
    QPushButton,
    QVBoxLayout,
    QWidget,
)



class LocationListWidget(QWidget):
    """List locations with add / browse / remove controls."""

    changed = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        header = QHBoxLayout()
        title = QLabel("Locations")
        title.setObjectName("SectionTitle")
        header.addWidget(title)
        header.addStretch(1)
        self.browse_btn = QPushButton("Browse…")
        self.browse_btn.setObjectName("AccentButton")
        self.browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_btn = QPushButton("Add path")
        self.add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        header.addWidget(self.add_btn)
        header.addWidget(self.browse_btn)
        layout.addLayout(header)

        hint = QLabel("Folders organize will scan for this rule")
        hint.setObjectName("HintLabel")
        layout.addWidget(hint)

        self.list_widget = QListWidget()
        self.list_widget.setMinimumHeight(80)
        self.list_widget.setMaximumHeight(120)
        layout.addWidget(self.list_widget)

        tools = QHBoxLayout()
        self.remove_btn = QPushButton("Remove")
        self.remove_btn.setObjectName("GhostButton")
        self.remove_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        tools.addWidget(self.remove_btn)
        tools.addStretch(1)
        layout.addLayout(tools)

        self.add_btn.clicked.connect(self._add_path)
        self.browse_btn.clicked.connect(self._browse)
        self.remove_btn.clicked.connect(self._remove)

    def set_locations(self, locations: List[str]) -> None:
        """Replace the list contents."""
        self.list_widget.clear()
        if not locations:
            self.list_widget.addItem("No folders yet — Browse or Add path")
            item = self.list_widget.item(0)
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            return
        self.list_widget.addItems(locations)

    def locations(self) -> List[str]:
        """Return the current location strings."""
        result: List[str] = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.flags() == Qt.ItemFlag.NoItemFlags:
                continue
            result.append(item.text())
        return result

    def _add_path(self) -> None:
        text, ok = QInputDialog.getText(self, "Add location", "Folder path:")
        if ok and text.strip():
            current = self.locations()
            current.append(text.strip())
            self.set_locations(current)
            self.changed.emit()

    def _browse(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Select folder")
        if path:
            current = self.locations()
            current.append(path)
            self.set_locations(current)
            self.changed.emit()

    def _remove(self) -> None:
        row = self.list_widget.currentRow()
        items = self.locations()
        if row < 0 or row >= len(items):
            return
        del items[row]
        self.set_locations(items)
        self.changed.emit()
