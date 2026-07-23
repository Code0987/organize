"""Single form field widget used inside filter/action editors."""

from __future__ import annotations

from typing import Any, List, Optional

from PyQt6.QtWidgets import (
    QCheckBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ui.schemas.field_spec import FieldSpec
from ui.styles.combo_fix import MenuSelect


class FormFieldWidget(QWidget):
    """Render and read one :class:`FieldSpec` as an appropriate Qt control."""

    def __init__(self, spec: FieldSpec, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.spec = spec
        self._editor: QWidget

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        if spec.field_type == "bool":
            self._editor = QCheckBox(spec.label)
            layout.addWidget(self._editor)
        else:
            form = QFormLayout()
            form.setContentsMargins(0, 0, 0, 0)
            self._editor = self._create_editor()
            form.addRow(spec.label, self._editor)
            layout.addLayout(form)

        if spec.help_text:
            help_label = QLabel(spec.help_text)
            help_label.setObjectName("HelpText")
            help_label.setWordWrap(True)
            layout.addWidget(help_label)

        if spec.default is not None:
            self.set_value(spec.default)

    def _create_editor(self) -> QWidget:
        ftype = self.spec.field_type
        if ftype == "choice":
            combo = MenuSelect()
            combo.addItems(list(self.spec.choices))
            return combo
        if ftype == "int":
            spin = QSpinBox()
            spin.setRange(-10_000_000, 10_000_000)
            return spin
        if ftype == "float":
            line = QLineEdit()
            line.setPlaceholderText("0.0")
            return line
        if ftype == "multiline":
            text = QTextEdit()
            text.setAcceptRichText(False)
            text.setMinimumHeight(80)
            return text
        if ftype == "list_str":
            line = QLineEdit()
            line.setPlaceholderText("comma or space separated")
            return line
        # default: str
        return QLineEdit()

    def set_value(self, value: Any) -> None:
        """Populate the control from a Python value."""
        editor = self._editor
        if isinstance(editor, QCheckBox):
            editor.setChecked(bool(value))
        elif isinstance(editor, MenuSelect):
            text = str(value)
            idx = editor.findText(text)
            if idx >= 0:
                editor.setCurrentIndex(idx)
        elif isinstance(editor, QSpinBox):
            try:
                editor.setValue(int(value))
            except (TypeError, ValueError):
                editor.setValue(0)
        elif isinstance(editor, QTextEdit):
            editor.setPlainText("" if value is None else str(value))
        elif isinstance(editor, QLineEdit):
            if isinstance(value, (list, set, tuple)):
                editor.setText(", ".join(str(v) for v in value))
            else:
                editor.setText("" if value is None else str(value))

    def value(self) -> Any:
        """Read the control into a Python value suitable for YAML params."""
        editor = self._editor
        ftype = self.spec.field_type
        if isinstance(editor, QCheckBox):
            return editor.isChecked()
        if isinstance(editor, MenuSelect):
            return editor.currentText()
        if isinstance(editor, QSpinBox):
            return editor.value()
        if isinstance(editor, QTextEdit):
            return editor.toPlainText()
        if isinstance(editor, QLineEdit):
            text = editor.text().strip()
            if ftype == "list_str":
                return self._split_list(text)
            if ftype == "float":
                if not text:
                    return 0.0
                return float(text)
            if ftype == "int":
                if not text:
                    return 0
                return int(text)
            return text
        return None

    @staticmethod
    def _split_list(text: str) -> List[str]:
        if not text:
            return []
        # Allow comma and/or whitespace separated values.
        parts: List[str] = []
        for chunk in text.replace(",", " ").split():
            if chunk:
                parts.append(chunk)
        return parts

    def is_empty(self) -> bool:
        """Return True when the field has no user-provided value."""
        value = self.value()
        if isinstance(value, bool):
            return False
        if isinstance(value, (list, set, tuple)):
            return len(value) == 0
        if isinstance(value, str):
            return value.strip() == ""
        if value is None:
            return True
        return False
