"""Split view: rule list on the left, interactive editor on the right."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List, Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QMessageBox,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from ui.models.rule_factory import RuleFactory
from ui.widgets.rule_detail import RuleDetail
from ui.widgets.rule_list import RuleList


class RuleWorkspace(QWidget):
    """Interactive rule editor (not a YAML text box)."""

    rules_changed = pyqtSignal(list)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.rules: List[Dict[str, Any]] = []
        self._factory = RuleFactory()
        self._updating = False

        splitter = QSplitter(Qt.Orientation.Horizontal)
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        self.list = RuleList()
        self.list.rule_selected.connect(self._show_rule)
        left_layout.addWidget(self.list, 1)

        buttons = QHBoxLayout()
        add = QPushButton("Add")
        dup = QPushButton("Duplicate")
        remove = QPushButton("Delete")
        up = QPushButton("Up")
        down = QPushButton("Down")
        add.clicked.connect(self.add_rule)
        dup.clicked.connect(self.duplicate_rule)
        remove.clicked.connect(self.delete_rule)
        up.clicked.connect(lambda: self.move_rule(-1))
        down.clicked.connect(lambda: self.move_rule(1))
        for button in (add, dup, remove, up, down):
            buttons.addWidget(button)
        left_layout.addLayout(buttons)

        self.detail = RuleDetail()
        self.detail.changed.connect(self._detail_changed)
        splitter.addWidget(left)
        splitter.addWidget(self.detail)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.addWidget(splitter)

    def set_rules(self, rules: List[Dict[str, Any]]) -> None:
        """Replace the in-memory rule list and refresh the UI."""
        self.rules = deepcopy(rules)
        current = self.list.currentRow()
        selected = 0
        if self.rules:
            selected = min(max(current, 0), len(self.rules) - 1)
        self.list.set_rules(self.rules, selected if self.rules else -1)
        if not self.rules:
            self.detail.load_rule(self._factory.new_rule())

    def _show_rule(self, row: int) -> None:
        if self._updating or row < 0 or row >= len(self.rules):
            return
        self.detail.load_rule(self.rules[row])

    def _detail_changed(self) -> None:
        row = self.list.currentRow()
        if row < 0 or row >= len(self.rules):
            return
        self.rules[row] = self.detail.to_rule()
        self._updating = True
        self.list.set_rules(self.rules, row)
        self._updating = False
        self.rules_changed.emit(deepcopy(self.rules))

    def add_rule(self) -> None:
        """Append a starter rule and select it."""
        self.rules.append(self._factory.new_rule(f"Rule {len(self.rules) + 1}"))
        self.list.set_rules(self.rules, len(self.rules) - 1)
        self.rules_changed.emit(deepcopy(self.rules))

    def duplicate_rule(self) -> None:
        """Clone the selected rule."""
        row = self.list.currentRow()
        if row < 0:
            return
        clone = deepcopy(self.rules[row])
        clone["name"] = f"{clone.get('name') or 'Rule'} copy"
        self.rules.insert(row + 1, clone)
        self.list.set_rules(self.rules, row + 1)
        self.rules_changed.emit(deepcopy(self.rules))

    def delete_rule(self) -> None:
        """Delete the selected rule after confirmation."""
        row = self.list.currentRow()
        if row < 0:
            return
        answer = QMessageBox.question(
            self,
            "Delete rule",
            "Delete the selected rule?",
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        del self.rules[row]
        next_row = min(row, len(self.rules) - 1) if self.rules else -1
        self.list.set_rules(self.rules, next_row)
        if not self.rules:
            self.detail.load_rule(self._factory.new_rule())
        self.rules_changed.emit(deepcopy(self.rules))

    def move_rule(self, delta: int) -> None:
        """Move the selected rule up (``-1``) or down (``1``)."""
        row = self.list.currentRow()
        dest = row + delta
        if row < 0 or dest < 0 or dest >= len(self.rules):
            return
        self.rules[row], self.rules[dest] = self.rules[dest], self.rules[row]
        self.list.set_rules(self.rules, dest)
        self.rules_changed.emit(deepcopy(self.rules))
