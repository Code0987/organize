"""List and form editor for rule filters."""

from __future__ import annotations

from typing import List, Optional

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from organize_gui.models.filter_data import FilterData
from organize_gui.models.filter_schemas import FILTER_SCHEMAS, filter_type_names, get_filter_schema
from organize_gui.widgets.dynamic_form import DynamicForm


class FilterListWidget(QWidget):
    """Interactive editor for a rule's filters.

    Signals:
        filters_changed: Emitted when filters are added, removed or edited.
    """

    filters_changed = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize the filter list UI."""
        super().__init__(parent)
        self._filters: List[FilterData] = []
        self._loading = False

        self._list = QListWidget(self)
        self._list.currentRowChanged.connect(self._on_selection)

        self._add_btn = QPushButton("Add", self)
        self._add_btn.clicked.connect(self._on_add)
        self._remove_btn = QPushButton("Remove", self)
        self._remove_btn.clicked.connect(self._on_remove)
        self._up_btn = QPushButton("↑", self)
        self._up_btn.setFixedWidth(32)
        self._up_btn.clicked.connect(lambda: self._move(-1))
        self._down_btn = QPushButton("↓", self)
        self._down_btn.setFixedWidth(32)
        self._down_btn.clicked.connect(lambda: self._move(1))

        btn_row = QHBoxLayout()
        btn_row.addWidget(self._add_btn)
        btn_row.addWidget(self._remove_btn)
        btn_row.addWidget(self._up_btn)
        btn_row.addWidget(self._down_btn)

        self._type_combo = QComboBox(self)
        for name in filter_type_names():
            schema = FILTER_SCHEMAS[name]
            self._type_combo.addItem(schema.label, name)
        self._type_combo.currentIndexChanged.connect(self._on_type_changed)

        self._inverted = QCheckBox("Invert (not …)", self)
        self._inverted.stateChanged.connect(self._on_inverted_changed)

        self._form = DynamicForm(self)
        self._form.values_changed.connect(self._on_form_changed)

        detail_layout = QFormLayout()
        detail_layout.addRow("Type", self._type_combo)
        detail_layout.addRow(self._inverted)

        detail_box = QGroupBox("Filter details", self)
        detail_v = QVBoxLayout(detail_box)
        detail_v.addLayout(detail_layout)
        detail_v.addWidget(self._form)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._list, stretch=1)
        layout.addLayout(btn_row)
        layout.addWidget(detail_box)

        self._set_detail_enabled(False)

    def set_filters(self, filters: List[FilterData]) -> None:
        """Load filters into the widget (kept by reference)."""
        self._filters = filters
        self._loading = True
        self._list.clear()
        for f in self._filters:
            self._list.addItem(QListWidgetItem(f.display_label()))
        self._loading = False
        if self._filters:
            self._list.setCurrentRow(0)
        else:
            self._set_detail_enabled(False)

    def filters(self) -> List[FilterData]:
        """Return the current filters list."""
        return self._filters

    def commit_pending_edits(self) -> None:
        """Flush the dynamic form into the selected filter's params."""
        if self._loading:
            return
        filt = self._current()
        if filt is None:
            return
        filt.params = self._form.get_values()
        self._refresh_current_label()

    def _set_detail_enabled(self, enabled: bool) -> None:
        """Enable or disable the detail form."""
        self._type_combo.setEnabled(enabled)
        self._inverted.setEnabled(enabled)
        self._form.setEnabled(enabled)

    def _current(self) -> Optional[FilterData]:
        """Return the selected filter, if any."""
        idx = self._list.currentRow()
        if 0 <= idx < len(self._filters):
            return self._filters[idx]
        return None

    def _on_selection(self, index: int) -> None:
        """Populate detail widgets for the selected filter."""
        if index < 0 or index >= len(self._filters):
            self._set_detail_enabled(False)
            return
        self._set_detail_enabled(True)
        filt = self._filters[index]
        self._loading = True
        schema = get_filter_schema(filt.name)
        type_idx = self._type_combo.findData(filt.name)
        if type_idx < 0:
            # Unknown type — add temporarily
            self._type_combo.addItem(filt.name, filt.name)
            type_idx = self._type_combo.findData(filt.name)
        self._type_combo.setCurrentIndex(type_idx)
        self._inverted.setChecked(filt.inverted)
        self._form.set_fields(schema.fields, filt.params)
        self._loading = False

    def _on_type_changed(self, _index: int) -> None:
        """Switch filter type and reset params to defaults."""
        if self._loading:
            return
        filt = self._current()
        if filt is None:
            return
        name = self._type_combo.currentData()
        if not name or name == filt.name:
            return
        schema = get_filter_schema(str(name))
        filt.name = str(name)
        filt.params = schema.default_params()
        self._loading = True
        self._form.set_fields(schema.fields, filt.params)
        self._loading = False
        self._refresh_current_label()
        self.filters_changed.emit()

    def _on_inverted_changed(self, *_args) -> None:
        """Toggle the inverted flag on the selected filter."""
        if self._loading:
            return
        filt = self._current()
        if filt is None:
            return
        filt.inverted = self._inverted.isChecked()
        self._refresh_current_label()
        self.filters_changed.emit()

    def _on_form_changed(self) -> None:
        """Copy form values into the selected filter's params."""
        if self._loading:
            return
        filt = self._current()
        if filt is None:
            return
        filt.params = self._form.get_values()
        self._refresh_current_label()
        self.filters_changed.emit()

    def _refresh_current_label(self) -> None:
        """Update the list label for the current filter."""
        idx = self._list.currentRow()
        if 0 <= idx < len(self._filters):
            item = self._list.item(idx)
            if item is not None:
                item.setText(self._filters[idx].display_label())

    def _on_add(self) -> None:
        """Add a default extension filter."""
        filt = FilterData.create_default("extension")
        self._filters.append(filt)
        self._list.addItem(QListWidgetItem(filt.display_label()))
        self._list.setCurrentRow(len(self._filters) - 1)
        self.filters_changed.emit()

    def _on_remove(self) -> None:
        """Remove the selected filter."""
        idx = self._list.currentRow()
        if idx < 0 or idx >= len(self._filters):
            return
        del self._filters[idx]
        self._list.takeItem(idx)
        self.filters_changed.emit()

    def _move(self, delta: int) -> None:
        """Move the selected filter up (delta=-1) or down (delta=1)."""
        idx = self._list.currentRow()
        new_idx = idx + delta
        if idx < 0 or new_idx < 0 or new_idx >= len(self._filters):
            return
        self._filters[idx], self._filters[new_idx] = (
            self._filters[new_idx],
            self._filters[idx],
        )
        # Refresh labels
        for i, f in enumerate(self._filters):
            item = self._list.item(i)
            if item is not None:
                item.setText(f.display_label())
        self._list.setCurrentRow(new_idx)
        self.filters_changed.emit()
