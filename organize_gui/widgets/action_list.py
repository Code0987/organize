"""List and form editor for rule actions."""

from __future__ import annotations

from typing import List, Optional

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
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

from organize_gui.models.action_data import ActionData
from organize_gui.models.action_schemas import ACTION_SCHEMAS, action_type_names, get_action_schema
from organize_gui.widgets.dynamic_form import DynamicForm


class ActionListWidget(QWidget):
    """Interactive editor for a rule's actions.

    Signals:
        actions_changed: Emitted when actions are added, removed or edited.
    """

    actions_changed = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize the action list UI."""
        super().__init__(parent)
        self._actions: List[ActionData] = []
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
        for name in action_type_names():
            schema = ACTION_SCHEMAS[name]
            self._type_combo.addItem(schema.label, name)
        self._type_combo.currentIndexChanged.connect(self._on_type_changed)

        self._form = DynamicForm(self)
        self._form.values_changed.connect(self._on_form_changed)

        detail_layout = QFormLayout()
        detail_layout.addRow("Type", self._type_combo)

        detail_box = QGroupBox("Action details", self)
        detail_v = QVBoxLayout(detail_box)
        detail_v.addLayout(detail_layout)
        detail_v.addWidget(self._form)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._list, stretch=1)
        layout.addLayout(btn_row)
        layout.addWidget(detail_box)

        self._set_detail_enabled(False)

    def set_actions(self, actions: List[ActionData]) -> None:
        """Load actions into the widget (kept by reference)."""
        self._actions = actions
        self._loading = True
        self._list.clear()
        for a in self._actions:
            self._list.addItem(QListWidgetItem(a.display_label()))
        self._loading = False
        if self._actions:
            self._list.setCurrentRow(0)
        else:
            self._set_detail_enabled(False)

    def actions(self) -> List[ActionData]:
        """Return the current actions list."""
        return self._actions

    def commit_pending_edits(self) -> None:
        """Flush the dynamic form into the selected action's params."""
        if self._loading:
            return
        action = self._current()
        if action is None:
            return
        action.params = self._form.get_values()
        self._refresh_current_label()

    def _set_detail_enabled(self, enabled: bool) -> None:
        """Enable or disable the detail form."""
        self._type_combo.setEnabled(enabled)
        self._form.setEnabled(enabled)

    def _current(self) -> Optional[ActionData]:
        """Return the selected action, if any."""
        idx = self._list.currentRow()
        if 0 <= idx < len(self._actions):
            return self._actions[idx]
        return None

    def _on_selection(self, index: int) -> None:
        """Populate detail widgets for the selected action."""
        if index < 0 or index >= len(self._actions):
            self._set_detail_enabled(False)
            return
        self._set_detail_enabled(True)
        action = self._actions[index]
        self._loading = True
        schema = get_action_schema(action.name)
        type_idx = self._type_combo.findData(action.name)
        if type_idx < 0:
            self._type_combo.addItem(action.name, action.name)
            type_idx = self._type_combo.findData(action.name)
        self._type_combo.setCurrentIndex(type_idx)
        self._form.set_fields(schema.fields, action.params)
        self._loading = False

    def _on_type_changed(self, _index: int) -> None:
        """Switch action type and reset params to defaults."""
        if self._loading:
            return
        action = self._current()
        if action is None:
            return
        name = self._type_combo.currentData()
        if not name or name == action.name:
            return
        schema = get_action_schema(str(name))
        action.name = str(name)
        action.params = schema.default_params()
        self._loading = True
        self._form.set_fields(schema.fields, action.params)
        self._loading = False
        self._refresh_current_label()
        self.actions_changed.emit()

    def _on_form_changed(self) -> None:
        """Copy form values into the selected action's params."""
        if self._loading:
            return
        action = self._current()
        if action is None:
            return
        action.params = self._form.get_values()
        self._refresh_current_label()
        self.actions_changed.emit()

    def _refresh_current_label(self) -> None:
        """Update the list label for the current action."""
        idx = self._list.currentRow()
        if 0 <= idx < len(self._actions):
            item = self._list.item(idx)
            if item is not None:
                item.setText(self._actions[idx].display_label())

    def _on_add(self) -> None:
        """Add a default echo action."""
        action = ActionData.create_default("echo")
        self._actions.append(action)
        self._list.addItem(QListWidgetItem(action.display_label()))
        self._list.setCurrentRow(len(self._actions) - 1)
        self.actions_changed.emit()

    def _on_remove(self) -> None:
        """Remove the selected action."""
        idx = self._list.currentRow()
        if idx < 0 or idx >= len(self._actions):
            return
        del self._actions[idx]
        self._list.takeItem(idx)
        self.actions_changed.emit()

    def _move(self, delta: int) -> None:
        """Move the selected action up or down."""
        idx = self._list.currentRow()
        new_idx = idx + delta
        if idx < 0 or new_idx < 0 or new_idx >= len(self._actions):
            return
        self._actions[idx], self._actions[new_idx] = (
            self._actions[new_idx],
            self._actions[idx],
        )
        for i, a in enumerate(self._actions):
            item = self._list.item(i)
            if item is not None:
                item.setText(a.display_label())
        self._list.setCurrentRow(new_idx)
        self.actions_changed.emit()
