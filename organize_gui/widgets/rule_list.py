"""Sidebar list of rules with add / remove / reorder controls."""

from __future__ import annotations

from typing import List, Optional

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from organize_gui.models.rule_data import RuleData


class RuleListWidget(QWidget):
    """List of rules with buttons to add, remove and reorder.

    Signals:
        selection_changed: Emitted with the selected rule index (or -1).
        rules_modified: Emitted when the rule list structure changes.
    """

    selection_changed = pyqtSignal(int)
    rules_modified = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize the rule list UI."""
        super().__init__(parent)
        self._rules: List[RuleData] = []

        self._list = QListWidget(self)
        self._list.currentRowChanged.connect(self.selection_changed.emit)

        self._add_btn = QPushButton("Add", self)
        self._add_btn.clicked.connect(self._on_add)
        self._remove_btn = QPushButton("Remove", self)
        self._remove_btn.clicked.connect(self._on_remove)
        self._up_btn = QPushButton("↑", self)
        self._up_btn.setFixedWidth(32)
        self._up_btn.clicked.connect(self._on_move_up)
        self._down_btn = QPushButton("↓", self)
        self._down_btn.setFixedWidth(32)
        self._down_btn.clicked.connect(self._on_move_down)

        btn_row = QHBoxLayout()
        btn_row.addWidget(self._add_btn)
        btn_row.addWidget(self._remove_btn)
        btn_row.addWidget(self._up_btn)
        btn_row.addWidget(self._down_btn)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._list)
        layout.addLayout(btn_row)

    def set_rules(self, rules: List[RuleData], select_index: int = 0) -> None:
        """Replace the displayed rules.

        Args:
            rules: New rule list (kept by reference).
            select_index: Index to select after refresh.
        """
        self._rules = rules
        self._refresh_labels()
        if self._rules:
            self._list.setCurrentRow(max(0, min(select_index, len(self._rules) - 1)))
        else:
            self._list.setCurrentRow(-1)

    def rules(self) -> List[RuleData]:
        """Return the current rule list (same object as set)."""
        return self._rules

    def current_index(self) -> int:
        """Return the currently selected row index, or -1."""
        return self._list.currentRow()

    def refresh_current_label(self) -> None:
        """Update the label of the currently selected rule."""
        idx = self._list.currentRow()
        if 0 <= idx < len(self._rules):
            item = self._list.item(idx)
            if item is not None:
                item.setText(self._rules[idx].display_label())

    def _refresh_labels(self) -> None:
        """Rebuild list items from the rule list."""
        current = self._list.currentRow()
        self._list.blockSignals(True)
        self._list.clear()
        for rule in self._rules:
            self._list.addItem(QListWidgetItem(rule.display_label()))
        self._list.blockSignals(False)
        if self._rules and current >= 0:
            self._list.setCurrentRow(min(current, len(self._rules) - 1))

    def _on_add(self) -> None:
        """Append a default rule and select it."""
        rule = RuleData.create_default()
        self._rules.append(rule)
        self._list.addItem(QListWidgetItem(rule.display_label()))
        self._list.setCurrentRow(len(self._rules) - 1)
        self.rules_modified.emit()

    def _on_remove(self) -> None:
        """Remove the selected rule."""
        idx = self._list.currentRow()
        if idx < 0 or idx >= len(self._rules):
            return
        del self._rules[idx]
        self._list.takeItem(idx)
        self.rules_modified.emit()
        if self._rules:
            self._list.setCurrentRow(min(idx, len(self._rules) - 1))
        else:
            self.selection_changed.emit(-1)

    def _on_move_up(self) -> None:
        """Move the selected rule one position up."""
        idx = self._list.currentRow()
        if idx <= 0:
            return
        self._rules[idx - 1], self._rules[idx] = self._rules[idx], self._rules[idx - 1]
        self._refresh_labels()
        self._list.setCurrentRow(idx - 1)
        self.rules_modified.emit()

    def _on_move_down(self) -> None:
        """Move the selected rule one position down."""
        idx = self._list.currentRow()
        if idx < 0 or idx >= len(self._rules) - 1:
            return
        self._rules[idx + 1], self._rules[idx] = self._rules[idx], self._rules[idx + 1]
        self._refresh_labels()
        self._list.setCurrentRow(idx + 1)
        self.rules_modified.emit()
