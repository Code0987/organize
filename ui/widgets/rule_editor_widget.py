"""Form editor for a single organize rule (interactive, not raw YAML)."""

from __future__ import annotations

from typing import List, Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from ui.models.rule_item import RuleItem
from ui.styles.combo_fix import MenuSelect
from ui.widgets.location_list_widget import LocationListWidget
from ui.widgets.pipeline_list_widget import PipelineListWidget


class RuleEditorWidget(QWidget):
    """Edit one :class:`RuleItem` with structured controls."""

    changed = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._rule: Optional[RuleItem] = None
        self._loading = False

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.placeholder = QLabel(
            "Select a rule on the left,\nor click + Add to create one."
        )
        self.placeholder.setObjectName("EmptyState")
        self.placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(self.placeholder)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.editor_host = QWidget()
        editor_layout = QVBoxLayout(self.editor_host)
        editor_layout.setContentsMargins(4, 4, 12, 16)
        editor_layout.setSpacing(16)

        # Header: name + enabled
        header = QVBoxLayout()
        header.setSpacing(6)
        name_label = QLabel("Rule name")
        name_label.setObjectName("HintLabel")
        self.name_edit = QLineEdit()
        self.name_edit.setObjectName("RuleNameEdit")
        self.name_edit.setPlaceholderText("e.g. Sort PDFs from Downloads")
        header.addWidget(name_label)
        header.addWidget(self.name_edit)

        toggles = QHBoxLayout()
        toggles.setSpacing(16)
        self.enabled_check = QCheckBox("Enabled")
        self.subfolders_check = QCheckBox("Include subfolders")
        toggles.addWidget(self.enabled_check)
        toggles.addWidget(self.subfolders_check)
        toggles.addStretch(1)
        header.addLayout(toggles)
        editor_layout.addLayout(header)

        # Options row
        options = QFrame()
        options.setObjectName("OptionsCard")
        options_layout = QFormLayout(options)
        options_layout.setContentsMargins(14, 12, 14, 12)
        options_layout.setHorizontalSpacing(16)
        options_layout.setVerticalSpacing(10)
        self.targets_combo = MenuSelect()
        self.targets_combo.addItem("Files", "files")
        self.targets_combo.addItem("Folders", "dirs")
        self.filter_mode_combo = MenuSelect()
        self.filter_mode_combo.addItem("All filters must match", "all")
        self.filter_mode_combo.addItem("Any filter may match", "any")
        self.filter_mode_combo.addItem("No filters may match", "none")
        self.tags_edit = QLineEdit()
        self.tags_edit.setPlaceholderText("optional, comma-separated")
        options_layout.addRow("Apply to", self.targets_combo)
        options_layout.addRow("Filter mode", self.filter_mode_combo)
        options_layout.addRow("Tags", self.tags_edit)
        editor_layout.addWidget(options)

        # Locations
        self.locations = LocationListWidget()
        editor_layout.addWidget(self.locations)

        # Filters / actions
        self.filters = PipelineListWidget("filter")
        editor_layout.addWidget(self.filters)

        self.actions = PipelineListWidget("action")
        editor_layout.addWidget(self.actions)

        editor_layout.addStretch(1)
        self.scroll.setWidget(self.editor_host)
        root.addWidget(self.scroll)
        self.scroll.hide()

        # Wire change signals
        self.name_edit.textChanged.connect(self._on_field_changed)
        self.enabled_check.toggled.connect(self._on_field_changed)
        self.targets_combo.currentIndexChanged.connect(self._on_field_changed)
        self.subfolders_check.toggled.connect(self._on_field_changed)
        self.filter_mode_combo.currentIndexChanged.connect(self._on_field_changed)
        self.tags_edit.textChanged.connect(self._on_field_changed)
        self.locations.changed.connect(self._on_field_changed)
        self.filters.changed.connect(self._on_field_changed)
        self.actions.changed.connect(self._on_field_changed)

    def set_rule(self, rule: Optional[RuleItem]) -> None:
        """Load *rule* into the form (or show the empty placeholder)."""
        self._rule = rule
        self._loading = True
        try:
            if rule is None:
                self.scroll.hide()
                self.placeholder.show()
                return
            self.placeholder.hide()
            self.scroll.show()
            self.name_edit.setText(rule.name)
            self.enabled_check.setChecked(rule.enabled)
            self._set_combo_data(self.targets_combo, rule.targets)
            self.subfolders_check.setChecked(rule.subfolders)
            self._set_combo_data(self.filter_mode_combo, rule.filter_mode)
            self.tags_edit.setText(", ".join(rule.tags))
            self.locations.set_locations(rule.locations)
            self.filters.set_items(rule.filters)
            self.actions.set_items(rule.actions)
        finally:
            self._loading = False

    def commit_to_rule(self) -> None:
        """Write form values back into the bound :class:`RuleItem`."""
        if self._rule is None:
            return
        self._rule.name = self.name_edit.text().strip() or "Unnamed rule"
        self._rule.enabled = self.enabled_check.isChecked()
        targets = self.targets_combo.currentData()
        self._rule.targets = "dirs" if targets == "dirs" else "files"
        self._rule.subfolders = self.subfolders_check.isChecked()
        mode = self.filter_mode_combo.currentData()
        if mode in ("all", "any", "none"):
            self._rule.filter_mode = mode  # type: ignore[assignment]
        self._rule.tags = self._parse_tags(self.tags_edit.text())
        self._rule.locations = self.locations.locations()
        self._rule.filters = self.filters.items()
        self._rule.actions = self.actions.items()

    def _on_field_changed(self, *_args: object) -> None:
        if self._loading or self._rule is None:
            return
        self.commit_to_rule()
        self.changed.emit()

    @staticmethod
    def _set_combo_data(combo: MenuSelect, value: str) -> None:
        idx = combo.findData(value)
        if idx >= 0:
            combo.setCurrentIndex(idx)

    @staticmethod
    def _parse_tags(text: str) -> List[str]:
        return [part.strip() for part in text.split(",") if part.strip()]
