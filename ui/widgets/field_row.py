"""One labeled form field for a filter or action parameter."""

from __future__ import annotations

from typing import Any, List, Optional

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ui.models.field_spec import FieldSpec
from ui.widgets.scroll_combo_box import ScrollComboBox
from ui.widgets.scroll_spin_box import ScrollSpinBox


class FieldRow(QWidget):
    """Render a :class:`FieldSpec` as the matching input widget."""

    changed = pyqtSignal()

    def __init__(self, spec: FieldSpec, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.spec = spec
        self._path_edit: Optional[QLineEdit] = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(3)

        label = QLabel(spec.label)
        label.setStyleSheet("color: #94a3b8;")
        layout.addWidget(label)

        self.widget = self._build_widget(spec)
        layout.addWidget(self.widget)
        if spec.hint:
            hint = QLabel(spec.hint)
            hint.setStyleSheet("color: #64748b; font-size: 11px;")
            hint.setWordWrap(True)
            layout.addWidget(hint)

    def _build_widget(self, spec: FieldSpec) -> QWidget:
        if spec.kind == "textarea":
            widget = QTextEdit()
            widget.setPlaceholderText(spec.placeholder)
            widget.setFixedHeight(72)
            widget.textChanged.connect(self.changed.emit)
            return widget
        if spec.kind == "bool":
            widget = QCheckBox("enabled")
            widget.stateChanged.connect(lambda _value: self.changed.emit())
            return widget
        if spec.kind == "choice":
            widget = ScrollComboBox()
            widget.addItems(list(spec.choices))
            widget.currentTextChanged.connect(lambda _text: self.changed.emit())
            return widget
        if spec.kind == "int":
            widget = ScrollSpinBox()
            widget.setRange(0, 100000)
            widget.valueChanged.connect(lambda _value: self.changed.emit())
            return widget
        if spec.kind == "path":
            row = QWidget()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 0, 0, 0)
            edit = QLineEdit()
            edit.setPlaceholderText(spec.placeholder)
            edit.textChanged.connect(lambda _text: self.changed.emit())
            browse = QPushButton("…")
            browse.setFixedWidth(36)
            browse.clicked.connect(lambda: self._browse(edit))
            row_layout.addWidget(edit, 1)
            row_layout.addWidget(browse)
            self._path_edit = edit
            return row

        widget = QLineEdit()
        widget.setPlaceholderText(spec.placeholder)
        widget.textChanged.connect(lambda _text: self.changed.emit())
        return widget

    def _browse(self, edit: QLineEdit) -> None:
        chosen = QFileDialog.getExistingDirectory(self, "Choose folder")
        if chosen:
            edit.setText(chosen.rstrip("/") + "/")

    def set_value(self, value: Any) -> None:
        """Populate the widget from a YAML value."""
        kind = self.spec.kind
        if kind == "textarea":
            self.widget.setPlainText(self._as_text(value))
        elif kind == "bool":
            self.widget.setChecked(
                bool(value) if value is not None else bool(self.spec.default)
            )
        elif kind == "choice":
            text = self._as_text(value) if value not in (None, "") else str(self.spec.default or "")
            index = self.widget.findText(text)
            if index >= 0:
                self.widget.setCurrentIndex(index)
        elif kind == "int":
            try:
                self.widget.setValue(int(value or 0))
            except (TypeError, ValueError):
                self.widget.setValue(0)
        elif kind == "path" and self._path_edit is not None:
            self._path_edit.setText(self._as_text(value))
        else:
            self.widget.setText(self._as_text(value))

    def value(self) -> Any:
        """Read the current widget value in YAML-ready form."""
        kind = self.spec.kind
        if kind == "textarea":
            return self.widget.toPlainText()
        if kind == "bool":
            return self.widget.isChecked()
        if kind == "choice":
            return self.widget.currentText()
        if kind == "int":
            return self.widget.value()
        if kind == "path" and self._path_edit is not None:
            return self._path_edit.text().strip()
        text = self.widget.text().strip()
        if kind == "list":
            return self._as_list(text)
        return text

    @staticmethod
    def _as_list(value: Any) -> List[str]:
        if value is None or value == "":
            return []
        if isinstance(value, (list, tuple, set)):
            return [str(item) for item in value]
        return [
            part.strip()
            for part in str(value).replace(",", " ").split()
            if part.strip()
        ]

    @staticmethod
    def _as_text(value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, (list, tuple, set)):
            return ", ".join(str(item) for item in value)
        return str(value)
