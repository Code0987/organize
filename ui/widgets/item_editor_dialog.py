"""Dialog for creating or editing a filter/action with a form UI."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from PyQt6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QMessageBox,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from ui.models.pipeline_item import ItemKind, PipelineItem
from ui.schemas.catalog import action_schema, filter_schema, list_action_names, list_filter_names
from ui.schemas.field_spec import ItemSchema
from ui.styles.combo_fix import MenuSelect
from ui.widgets.form_field_widget import FormFieldWidget


class ItemEditorDialog(QDialog):
    """Interactive editor for a single filter or action."""

    def __init__(
        self,
        kind: ItemKind,
        item: Optional[PipelineItem] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.kind = kind
        self._item = item
        self._field_widgets: List[FormFieldWidget] = []

        title = "Edit" if item else "Add"
        self.setWindowTitle(f"{title} {kind}")
        self.resize(480, 520)

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        form = QFormLayout()
        form.setSpacing(10)
        self.type_combo = MenuSelect()
        names = list_filter_names() if kind == "filter" else list_action_names()
        for name in names:
            schema = filter_schema(name) if kind == "filter" else action_schema(name)
            self.type_combo.addItem(f"{schema.label} ({name})", name)
        form.addRow("Type", self.type_combo)

        self.invert_check = QCheckBox("Invert (not …)")
        self.invert_check.setVisible(kind == "filter")
        form.addRow("", self.invert_check)

        self.description_label = QLabel("")
        self.description_label.setWordWrap(True)
        form.addRow("About", self.description_label)
        root.addLayout(form)

        self.fields_host = QWidget()
        self.fields_layout = QVBoxLayout(self.fields_host)
        self.fields_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.fields_host)
        root.addWidget(scroll, stretch=1)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

        self.type_combo.currentIndexChanged.connect(self._rebuild_fields)

        if item is not None:
            idx = self.type_combo.findData(item.name)
            if idx >= 0:
                self.type_combo.setCurrentIndex(idx)
            self.invert_check.setChecked(item.inverted)
        self._rebuild_fields()
        if item is not None:
            self._populate_from_item(item)

    def _current_schema(self) -> ItemSchema:
        name = self.type_combo.currentData()
        if self.kind == "filter":
            return filter_schema(str(name))
        return action_schema(str(name))

    def _rebuild_fields(self) -> None:
        while self.fields_layout.count():
            child = self.fields_layout.takeAt(0)
            widget = child.widget()
            if widget is not None:
                widget.deleteLater()
        self._field_widgets.clear()

        schema = self._current_schema()
        self.description_label.setText(schema.description)
        self.invert_check.setEnabled(schema.supports_invert)
        if not schema.supports_invert:
            self.invert_check.setChecked(False)

        if not schema.fields:
            empty = QLabel("This item has no parameters.")
            empty.setObjectName("HintLabel")
            self.fields_layout.addWidget(empty)
        else:
            for spec in schema.fields:
                field_widget = FormFieldWidget(spec)
                self._field_widgets.append(field_widget)
                self.fields_layout.addWidget(field_widget)
        self.fields_layout.addStretch(1)

    def _populate_from_item(self, item: PipelineItem) -> None:
        schema = self._current_schema()
        values: Dict[str, Any] = dict(item.params)
        if item.primary_value is not None:
            primary = schema.primary_field()
            if primary is not None:
                values.setdefault(primary.name, item.primary_value)
            else:
                # Best-effort: put shorthand into the first field.
                if schema.fields:
                    values.setdefault(schema.fields[0].name, item.primary_value)

        for widget in self._field_widgets:
            if widget.spec.name in values:
                widget.set_value(values[widget.spec.name])

    def _on_accept(self) -> None:
        try:
            self.result_item()
        except ValueError as exc:
            QMessageBox.warning(self, "Invalid values", str(exc))
            return
        self.accept()

    def result_item(self) -> PipelineItem:
        """Build a :class:`PipelineItem` from the current form state."""
        schema = self._current_schema()
        params: Dict[str, Any] = {}

        for widget in self._field_widgets:
            spec = widget.spec
            if widget.is_empty():
                if spec.required:
                    raise ValueError(f"'{spec.label}' is required.")
                continue
            value = widget.value()
            # Skip int defaults of 0 for time filters to keep YAML clean? Keep them
            # only if non-default for cleaner output when possible.
            if spec.field_type in {"int", "float"} and value == 0 and not spec.required:
                # Still include if user explicitly cares — keep non-zero only.
                continue
            if spec.field_type == "bool" and value == spec.default:
                continue
            if spec.field_type == "choice" and value == spec.default and not spec.required:
                continue
            if spec.field_type == "str" and value == (spec.default or ""):
                if not spec.required:
                    continue
            params[spec.name] = value

        # Shorthand: single primary field and nothing else → primary_value form.
        primary = schema.primary_field()
        primary_value = None
        final_params = dict(params)
        if primary and set(params.keys()) == {primary.name}:
            primary_value = params[primary.name]
            # For extension filter, list of one can stay as primary list/string.
            final_params = {}
        elif not params and not schema.allow_empty and schema.fields:
            # If all optional and empty but item needs something
            required = [f for f in schema.fields if f.required]
            if required:
                raise ValueError(f"Please fill: {required[0].label}")

        if not params and not schema.allow_empty and primary is None and schema.fields:
            # allow if only optional defaults omitted
            pass

        return PipelineItem(
            kind=self.kind,
            name=schema.name,
            params=final_params if primary_value is None else {},
            inverted=self.invert_check.isChecked() and schema.supports_invert,
            primary_value=primary_value,
        )
