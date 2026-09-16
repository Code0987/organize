"""Interactive editor for a single filter or action."""

from __future__ import annotations

from typing import Any, Dict, Optional

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ui.models.catalog import Catalog
from ui.models.item_spec import ItemSpec
from ui.models.named_entry import NamedEntry
from ui.widgets.field_row import FieldRow
from ui.widgets.scroll_combo_box import ScrollComboBox


class NamedItemEditor(QWidget):
    """Type combo + invert checkbox + parameter fields for one item."""

    changed = pyqtSignal()
    remove_requested = pyqtSignal()

    def __init__(self, kind: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.kind = kind  # "filter" or "action"
        self.catalog = Catalog()
        self.rows: Dict[str, FieldRow] = {}

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 8, 8)

        header = QHBoxLayout()
        self.invert = QCheckBox("not")
        self.invert.setVisible(kind == "filter")
        self.invert.stateChanged.connect(lambda _value: self.changed.emit())
        self.combo = ScrollComboBox()
        names = (
            self.catalog.filter_names()
            if kind == "filter"
            else self.catalog.action_names()
        )
        self.combo.addItems(names)
        self.combo.currentTextChanged.connect(self._rebuild_fields)
        remove = QPushButton("Remove")
        remove.clicked.connect(self.remove_requested.emit)
        header.addWidget(self.invert)
        header.addWidget(self.combo, 1)
        header.addWidget(remove)
        outer.addLayout(header)

        self.summary = QLabel("")
        self.summary.setStyleSheet("color: #64748b;")
        self.summary.setWordWrap(True)
        outer.addWidget(self.summary)

        self.fields_host = QVBoxLayout()
        outer.addLayout(self.fields_host)
        self._rebuild_fields(self.combo.currentText())

    def spec(self) -> ItemSpec:
        """Schema for the currently selected type."""
        name = self.combo.currentText()
        if self.kind == "filter":
            return self.catalog.filter_spec(name)
        return self.catalog.action_spec(name)

    def _rebuild_fields(self, _name: str = "") -> None:
        while self.fields_host.count():
            item = self.fields_host.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self.rows.clear()
        spec = self.spec()
        self.summary.setText(spec.summary)
        self.invert.setEnabled(spec.can_invert)
        for field in spec.fields:
            row = FieldRow(field)
            row.changed.connect(self.changed.emit)
            self.rows[field.key] = row
            self.fields_host.addWidget(row)
        self.changed.emit()

    def set_entry(self, entry: Any) -> None:
        """Load a YAML list item into the form."""
        try:
            parsed = NamedEntry.parse(entry)
        except ValueError:
            return
        blocked = self.combo.blockSignals(True)
        if self.combo.findText(parsed.name) < 0:
            self.combo.addItem(parsed.name)
        self.combo.setCurrentText(parsed.name)
        self.combo.blockSignals(blocked)
        self._rebuild_fields(parsed.name)
        self.invert.setChecked(parsed.inverted)
        spec = self.spec()
        if parsed.value is None:
            params: Dict[str, Any] = {}
        elif isinstance(parsed.value, dict):
            params = dict(parsed.value)
        elif spec.fields:
            params = {spec.fields[0].key: parsed.value}
        else:
            params = {}
        for key, row in self.rows.items():
            row.set_value(params.get(key, row.spec.default))

    def to_entry(self) -> Any:
        """Serialize the form back to a YAML list item."""
        spec = self.spec()
        params = {key: row.value() for key, row in self.rows.items()}
        return NamedEntry.from_params(spec, params, self.invert.isChecked()).emit()
