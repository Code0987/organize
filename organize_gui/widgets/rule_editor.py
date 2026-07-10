"""Full interactive editor for a single organize rule."""

from __future__ import annotations

from typing import Optional, Set

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from organize_gui.models.rule_data import RuleData
from organize_gui.widgets.action_list import ActionListWidget
from organize_gui.widgets.filter_list import FilterListWidget
from organize_gui.widgets.location_list import LocationListWidget


class RuleEditorWidget(QWidget):
    """Form-based editor covering all options of one rule.

    Signals:
        rule_changed: Emitted whenever any field of the rule changes.
    """

    rule_changed = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize the rule editor layout."""
        super().__init__(parent)
        self._rule: Optional[RuleData] = None
        self._loading = False

        # --- general options ---
        self._name_edit = QLineEdit(self)
        self._name_edit.setPlaceholderText("Optional rule name")
        self._name_edit.textChanged.connect(self._on_general_changed)

        self._enabled = QCheckBox("Enabled", self)
        self._enabled.setChecked(True)
        self._enabled.stateChanged.connect(self._on_general_changed)

        self._targets = QComboBox(self)
        self._targets.addItem("Files", "files")
        self._targets.addItem("Directories", "dirs")
        self._targets.currentIndexChanged.connect(self._on_general_changed)

        self._subfolders = QCheckBox("Include subfolders", self)
        self._subfolders.stateChanged.connect(self._on_general_changed)

        self._filter_mode = QComboBox(self)
        self._filter_mode.addItem("All filters must match", "all")
        self._filter_mode.addItem("Any filter may match", "any")
        self._filter_mode.addItem("No filters may match", "none")
        self._filter_mode.currentIndexChanged.connect(self._on_general_changed)

        self._tags_edit = QLineEdit(self)
        self._tags_edit.setPlaceholderText("comma-separated tags, e.g. cleanup, photos")
        # textChanged keeps the model in sync even when Save/Run is clicked
        # while the field still has focus (editingFinished would not fire).
        self._tags_edit.textChanged.connect(self._on_general_changed)

        general_form = QFormLayout()
        general_form.addRow("Name", self._name_edit)
        general_form.addRow(self._enabled)
        general_form.addRow("Targets", self._targets)
        general_form.addRow(self._subfolders)
        general_form.addRow("Filter mode", self._filter_mode)
        general_form.addRow("Tags", self._tags_edit)

        general_box = QGroupBox("Rule options", self)
        general_box.setLayout(general_form)

        # --- locations / filters / actions ---
        self._locations = LocationListWidget(self)
        self._locations.locations_changed.connect(self._on_child_changed)

        self._filters = FilterListWidget(self)
        self._filters.filters_changed.connect(self._on_child_changed)

        self._actions = ActionListWidget(self)
        self._actions.actions_changed.connect(self._on_child_changed)

        loc_box = QGroupBox("Locations", self)
        loc_layout = QVBoxLayout(loc_box)
        loc_layout.addWidget(self._locations)

        filt_box = QGroupBox("Filters", self)
        filt_layout = QVBoxLayout(filt_box)
        filt_layout.addWidget(self._filters)

        act_box = QGroupBox("Actions", self)
        act_layout = QVBoxLayout(act_box)
        act_layout.addWidget(self._actions)

        mid = QSplitter(self)
        mid.setChildrenCollapsible(False)
        mid.addWidget(loc_box)
        mid.addWidget(filt_box)
        mid.addWidget(act_box)
        mid.setStretchFactor(0, 1)
        mid.setStretchFactor(1, 1)
        mid.setStretchFactor(2, 1)

        self._placeholder = QLabel(
            "Select or add a rule to edit it interactively.",
            self,
        )
        self._placeholder.setStyleSheet("color: gray; font-style: italic; padding: 24px;")

        self._content = QWidget(self)
        content_layout = QVBoxLayout(self._content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.addWidget(general_box)
        content_layout.addWidget(mid, stretch=1)

        stack = QVBoxLayout(self)
        stack.setContentsMargins(0, 0, 0, 0)
        stack.addWidget(self._placeholder)
        stack.addWidget(self._content)
        self._content.hide()

    def set_rule(self, rule: Optional[RuleData]) -> None:
        """Load a rule into the editor, or clear when ``None``."""
        self._rule = rule
        if rule is None:
            self._content.hide()
            self._placeholder.show()
            return

        self._placeholder.hide()
        self._content.show()
        self._loading = True

        self._name_edit.setText(rule.name)
        self._enabled.setChecked(rule.enabled)
        t_idx = self._targets.findData(rule.targets)
        self._targets.setCurrentIndex(max(0, t_idx))
        self._subfolders.setChecked(rule.subfolders)
        fm_idx = self._filter_mode.findData(rule.filter_mode)
        self._filter_mode.setCurrentIndex(max(0, fm_idx))
        self._tags_edit.setText(", ".join(sorted(rule.tags)))

        self._locations.set_locations(rule.locations)
        self._filters.set_filters(rule.filters)
        self._actions.set_actions(rule.actions)

        self._loading = False

    def rule(self) -> Optional[RuleData]:
        """Return the rule currently being edited."""
        return self._rule

    def commit_pending_edits(self) -> None:
        """Flush in-progress form fields into the rule model.

        Call this before serializing, saving, validating, or running so that
        values typed into line edits are not lost when focus never left the field.
        """
        if self._rule is None:
            return
        self._on_general_changed()
        self._locations.commit_pending_edits()
        self._filters.commit_pending_edits()
        self._actions.commit_pending_edits()

    def _on_general_changed(self, *_args) -> None:
        """Sync general form fields into the rule model."""
        if self._loading or self._rule is None:
            return
        self._rule.name = self._name_edit.text().strip()
        self._rule.enabled = self._enabled.isChecked()
        targets = self._targets.currentData()
        self._rule.targets = targets if targets in ("files", "dirs") else "files"
        self._rule.subfolders = self._subfolders.isChecked()
        mode = self._filter_mode.currentData()
        self._rule.filter_mode = mode if mode in ("all", "any", "none") else "all"
        tags: Set[str] = {
            t.strip() for t in self._tags_edit.text().split(",") if t.strip()
        }
        self._rule.tags = tags
        self.rule_changed.emit()

    def _on_child_changed(self) -> None:
        """Propagate nested editor changes."""
        if self._loading or self._rule is None:
            return
        self.rule_changed.emit()
