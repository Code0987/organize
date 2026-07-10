"""List editor for rule locations with path browsing."""

from __future__ import annotations

from typing import List, Optional

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from organize_gui.models.location_data import LocationData
from organize_gui.widgets.path_picker import PathPicker


class LocationListWidget(QWidget):
    """Interactive editor for a rule's locations list.

    Signals:
        locations_changed: Emitted when locations are added, removed or edited.
    """

    locations_changed = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize the location list UI."""
        super().__init__(parent)
        self._locations: List[LocationData] = []
        self._loading = False

        self._list = QListWidget(self)
        self._list.currentRowChanged.connect(self._on_selection)

        self._add_btn = QPushButton("Add", self)
        self._add_btn.clicked.connect(self._on_add)
        self._remove_btn = QPushButton("Remove", self)
        self._remove_btn.clicked.connect(self._on_remove)

        list_btns = QHBoxLayout()
        list_btns.addWidget(self._add_btn)
        list_btns.addWidget(self._remove_btn)

        # Detail form for selected location
        self._path_picker = PathPicker(
            self,
            directory_mode=True,
            placeholder="~/Downloads",
        )
        self._path_picker.path_changed.connect(self._on_path_changed)

        self._sub_hint = QLabel(
            "Tip: set subfolders on the rule to recurse into children.",
            self,
        )
        self._sub_hint.setStyleSheet("color: gray; font-size: 11px;")

        self._min_depth = QSpinBox(self)
        self._min_depth.setRange(0, 100)
        self._min_depth.valueChanged.connect(self._on_detail_changed)

        self._max_depth = QLineEdit(self)
        self._max_depth.setPlaceholderText("inherit, number, or empty for unlimited")
        self._max_depth.textChanged.connect(self._on_detail_changed)

        self._exclude_files = QLineEdit(self)
        self._exclude_files.setPlaceholderText("comma-separated globs")
        self._exclude_files.textChanged.connect(self._on_detail_changed)

        self._exclude_dirs = QLineEdit(self)
        self._exclude_dirs.setPlaceholderText("comma-separated globs")
        self._exclude_dirs.textChanged.connect(self._on_detail_changed)

        self._ignore_errors = QCheckBox("Ignore walk errors", self)
        self._ignore_errors.stateChanged.connect(self._on_detail_changed)

        detail_form = QFormLayout()
        detail_form.addRow("Path", self._path_picker)
        detail_form.addRow("Min depth", self._min_depth)
        detail_form.addRow("Max depth", self._max_depth)
        detail_form.addRow("Exclude files", self._exclude_files)
        detail_form.addRow("Exclude dirs", self._exclude_dirs)
        detail_form.addRow(self._ignore_errors)

        detail_box = QGroupBox("Location details", self)
        detail_box.setLayout(detail_form)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._list, stretch=1)
        layout.addLayout(list_btns)
        layout.addWidget(detail_box)
        layout.addWidget(self._sub_hint)

        self._set_detail_enabled(False)

    def set_locations(self, locations: List[LocationData]) -> None:
        """Load locations into the widget (kept by reference)."""
        self._locations = locations
        self._loading = True
        self._list.clear()
        for loc in self._locations:
            self._list.addItem(QListWidgetItem(loc.display_label()))
        self._loading = False
        if self._locations:
            self._list.setCurrentRow(0)
        else:
            self._set_detail_enabled(False)

    def locations(self) -> List[LocationData]:
        """Return the current locations list."""
        return self._locations

    def commit_pending_edits(self) -> None:
        """Flush detail form fields into the selected location model."""
        if self._current() is not None:
            self._on_detail_changed()

    def _set_detail_enabled(self, enabled: bool) -> None:
        """Enable or disable the detail form."""
        for w in (
            self._path_picker,
            self._min_depth,
            self._max_depth,
            self._exclude_files,
            self._exclude_dirs,
            self._ignore_errors,
        ):
            w.setEnabled(enabled)

    def _on_selection(self, index: int) -> None:
        """Populate the detail form when the list selection changes."""
        if index < 0 or index >= len(self._locations):
            self._set_detail_enabled(False)
            return
        self._set_detail_enabled(True)
        loc = self._locations[index]
        self._loading = True
        self._path_picker.set_text(loc.path[0] if loc.path else "")
        self._min_depth.setValue(loc.min_depth)
        if loc.max_depth is None:
            self._max_depth.setText("")
        else:
            self._max_depth.setText(str(loc.max_depth))
        self._exclude_files.setText(", ".join(loc.exclude_files))
        self._exclude_dirs.setText(", ".join(loc.exclude_dirs))
        self._ignore_errors.setChecked(loc.ignore_errors)
        self._loading = False

    def _current(self) -> Optional[LocationData]:
        """Return the selected location, if any."""
        idx = self._list.currentRow()
        if 0 <= idx < len(self._locations):
            return self._locations[idx]
        return None

    def _on_path_changed(self, text: str) -> None:
        """Update the path on the selected location."""
        if self._loading:
            return
        loc = self._current()
        if loc is None:
            return
        loc.path = [text] if text else []
        item = self._list.currentItem()
        if item is not None:
            item.setText(loc.display_label())
        self.locations_changed.emit()

    def _on_detail_changed(self, *_args) -> None:
        """Sync detail form fields back into the selected location."""
        if self._loading:
            return
        loc = self._current()
        if loc is None:
            return
        loc.min_depth = self._min_depth.value()
        max_text = self._max_depth.text().strip()
        if max_text == "":
            loc.max_depth = None
        elif max_text == "inherit":
            loc.max_depth = "inherit"
        else:
            try:
                loc.max_depth = int(max_text)
            except ValueError:
                loc.max_depth = max_text  # type: ignore[assignment]
        loc.exclude_files = [
            p.strip() for p in self._exclude_files.text().split(",") if p.strip()
        ]
        loc.exclude_dirs = [
            p.strip() for p in self._exclude_dirs.text().split(",") if p.strip()
        ]
        loc.ignore_errors = self._ignore_errors.isChecked()
        self.locations_changed.emit()

    def _on_add(self) -> None:
        """Add a new location entry."""
        loc = LocationData(path=["~/Downloads"])
        self._locations.append(loc)
        self._list.addItem(QListWidgetItem(loc.display_label()))
        self._list.setCurrentRow(len(self._locations) - 1)
        self.locations_changed.emit()

    def _on_remove(self) -> None:
        """Remove the selected location."""
        idx = self._list.currentRow()
        if idx < 0 or idx >= len(self._locations):
            return
        del self._locations[idx]
        self._list.takeItem(idx)
        self.locations_changed.emit()
