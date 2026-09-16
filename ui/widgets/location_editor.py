"""List of folders a rule should search."""

from __future__ import annotations

from typing import List, Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ui.models.location_preflight import LocationPreflight


class LocationEditor(QGroupBox):
    """Add / remove search locations with a folder picker."""

    changed = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__("Locations", parent)
        layout = QVBoxLayout(self)
        self.list = QListWidget()
        self.list.setMinimumHeight(90)
        layout.addWidget(self.list)
        self.hint = QLabel("Use Add folder to pick a folder that exists.")
        self.hint.setWordWrap(True)
        self.hint.setStyleSheet("color: #94a3b8; font-size: 11px;")
        layout.addWidget(self.hint)
        row = QHBoxLayout()
        add = QPushButton("Add folder")
        add.clicked.connect(self._add)
        remove = QPushButton("Remove")
        remove.clicked.connect(self._remove)
        row.addWidget(add)
        row.addWidget(remove)
        row.addStretch(1)
        layout.addLayout(row)

    def set_paths(self, paths: List[str]) -> None:
        """Replace the list with ``paths``."""
        self.list.clear()
        for path in paths:
            if path:
                self.list.addItem(path)
        self._refresh_hint()

    def paths(self) -> List[str]:
        """Return the current location strings, in order."""
        return [self.list.item(index).text() for index in range(self.list.count())]

    def _add(self) -> None:
        chosen = QFileDialog.getExistingDirectory(self, "Add location")
        if chosen:
            self.list.addItem(chosen)
            self._refresh_hint()
            self.changed.emit()

    def _remove(self) -> None:
        row = self.list.currentRow()
        if row >= 0:
            self.list.takeItem(row)
            self._refresh_hint()
            self.changed.emit()

    def _refresh_hint(self) -> None:
        """Show a warning if any listed folder does not exist."""
        preflight = LocationPreflight()
        missing = []
        for raw in self.paths():
            check = preflight.inspect_path("rule", raw)
            item_rows = self.list.findItems(raw, Qt.MatchFlag.MatchExactly)
            for item in item_rows:
                if not check.exists:
                    item.setToolTip(f"Does not exist: {check.resolved}")
                else:
                    item.setToolTip(str(check.resolved))
            if not check.exists:
                missing.append(str(check.resolved))
        if missing:
            self.hint.setText(
                "Missing folder: " + ", ".join(missing) + ". Dry run will match nothing."
            )
            self.hint.setStyleSheet("color: #fbbf24; font-size: 11px;")
        else:
            self.hint.setText("Use Add folder to pick a folder that exists.")
            self.hint.setStyleSheet("color: #94a3b8; font-size: 11px;")
