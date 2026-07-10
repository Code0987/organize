"""Dynamic form widget generated from a list of field definitions."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QSpinBox,
    QWidget,
)

from organize_gui.models.field_definition import FieldDefinition
from organize_gui.widgets.path_picker import PathPicker


class DynamicForm(QWidget):
    """Builds and manages input widgets for a list of :class:`FieldDefinition`.

    Signals:
        values_changed: Emitted whenever any field value changes.
    """

    values_changed = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize an empty form."""
        super().__init__(parent)
        self._fields: List[FieldDefinition] = []
        self._widgets: Dict[str, QWidget] = {}
        self._layout = QFormLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setFieldGrowthPolicy(
            QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow
        )

    def set_fields(
        self,
        fields: List[FieldDefinition],
        values: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Rebuild the form for the given fields and optional values.

        Args:
            fields: Field definitions driving the widgets.
            values: Initial parameter values keyed by field name.
        """
        self._clear()
        self._fields = list(fields)
        values = values or {}

        if not fields:
            label = QLabel("No parameters for this type.", self)
            label.setStyleSheet("color: gray; font-style: italic;")
            self._layout.addRow(label)
            return

        for fdef in fields:
            widget = self._create_widget(fdef)
            self._widgets[fdef.name] = widget
            initial = values.get(fdef.name, fdef.default)
            self._set_widget_value(fdef, widget, initial)

            label = QLabel(fdef.label + ("" if not fdef.required else " *"), self)
            if fdef.help_text:
                label.setToolTip(fdef.help_text)
                widget.setToolTip(fdef.help_text)
            self._layout.addRow(label, widget)

    def get_values(self) -> Dict[str, Any]:
        """Collect current field values into a params dict."""
        result: Dict[str, Any] = {}
        for fdef in self._fields:
            widget = self._widgets.get(fdef.name)
            if widget is None:
                continue
            result[fdef.name] = self._get_widget_value(fdef, widget)
        return result

    def _clear(self) -> None:
        """Remove all rows and widgets from the form."""
        while self._layout.rowCount():
            self._layout.removeRow(0)
        self._widgets.clear()
        self._fields.clear()

    def _create_widget(self, fdef: FieldDefinition) -> QWidget:
        """Create an input widget appropriate for the field type."""
        if fdef.field_type == "bool":
            widget = QCheckBox(self)
            widget.stateChanged.connect(lambda _=None: self.values_changed.emit())
            return widget

        if fdef.field_type == "int":
            widget = QSpinBox(self)
            widget.setRange(-999999, 999999)
            widget.valueChanged.connect(lambda _=None: self.values_changed.emit())
            return widget

        if fdef.field_type == "choice":
            widget = QComboBox(self)
            for choice in fdef.choices or []:
                widget.addItem(choice)
            widget.currentTextChanged.connect(lambda _=None: self.values_changed.emit())
            return widget

        if fdef.field_type == "text":
            widget = QPlainTextEdit(self)
            widget.setMaximumHeight(100)
            widget.textChanged.connect(self.values_changed.emit)
            return widget

        if fdef.field_type == "path":
            widget = PathPicker(self, directory_mode=True)
            widget.path_changed.connect(lambda _=None: self.values_changed.emit())
            return widget

        # str and list_str use a line edit (list_str is comma-separated)
        widget = QLineEdit(self)
        if fdef.field_type == "list_str":
            widget.setPlaceholderText("comma-separated values")
        widget.textChanged.connect(lambda _=None: self.values_changed.emit())
        return widget

    def _set_widget_value(
        self,
        fdef: FieldDefinition,
        widget: QWidget,
        value: Any,
    ) -> None:
        """Push a value into the given widget."""
        if isinstance(widget, QCheckBox):
            widget.setChecked(bool(value))
        elif isinstance(widget, QSpinBox):
            try:
                widget.setValue(int(value or 0))
            except (TypeError, ValueError):
                widget.setValue(0)
        elif isinstance(widget, QComboBox):
            text = str(value) if value is not None else ""
            idx = widget.findText(text)
            if idx >= 0:
                widget.setCurrentIndex(idx)
            elif text:
                widget.addItem(text)
                widget.setCurrentText(text)
        elif isinstance(widget, QPlainTextEdit):
            widget.setPlainText("" if value is None else str(value))
        elif isinstance(widget, PathPicker):
            widget.set_text("" if value is None else str(value))
        elif isinstance(widget, QLineEdit):
            if fdef.field_type == "list_str":
                if isinstance(value, list):
                    widget.setText(", ".join(str(v) for v in value))
                elif value is None:
                    widget.setText("")
                else:
                    widget.setText(str(value))
            else:
                widget.setText("" if value is None else str(value))

    def _get_widget_value(self, fdef: FieldDefinition, widget: QWidget) -> Any:
        """Read the current value from a widget."""
        if isinstance(widget, QCheckBox):
            return widget.isChecked()
        if isinstance(widget, QSpinBox):
            return widget.value()
        if isinstance(widget, QComboBox):
            return widget.currentText()
        if isinstance(widget, QPlainTextEdit):
            return widget.toPlainText()
        if isinstance(widget, PathPicker):
            return widget.text().strip()
        if isinstance(widget, QLineEdit):
            text = widget.text().strip()
            if fdef.field_type == "list_str":
                if not text:
                    return []
                return [p.strip() for p in text.split(",") if p.strip()]
            return text
        return None
