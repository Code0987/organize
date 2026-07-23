"""Sidebar list of rules in the open configuration."""

from __future__ import annotations

from typing import List, Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from ui.models.rule_item import RuleItem


class RuleListWidget(QWidget):
    """Shows rule names and supports add / remove / reorder / select."""

    selection_changed = pyqtSignal(int)
    changed = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._rules: List[RuleItem] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        header = QHBoxLayout()
        title = QLabel("Rules")
        title.setObjectName("PanelTitle")
        header.addWidget(title)
        header.addStretch(1)

        self.add_btn = QToolButton()
        self.add_btn.setText("+ Add")
        self.add_btn.setObjectName("AccentButton")
        self.add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        header.addWidget(self.add_btn)
        layout.addLayout(header)

        self.list_widget = QListWidget()
        self.list_widget.setObjectName("RuleList")
        self.list_widget.setSpacing(2)
        self.list_widget.setAlternatingRowColors(False)
        layout.addWidget(self.list_widget, stretch=1)

        tools = QHBoxLayout()
        tools.setSpacing(4)
        self.duplicate_btn = self._ghost("Duplicate")
        self.remove_btn = self._ghost("Remove")
        self.up_btn = self._ghost("↑")
        self.down_btn = self._ghost("↓")
        for btn in (self.duplicate_btn, self.remove_btn, self.up_btn, self.down_btn):
            tools.addWidget(btn)
        tools.addStretch(1)
        layout.addLayout(tools)

        self.add_btn.clicked.connect(self._add)
        self.duplicate_btn.clicked.connect(self._duplicate)
        self.remove_btn.clicked.connect(self._remove)
        self.up_btn.clicked.connect(lambda: self._move(-1))
        self.down_btn.clicked.connect(lambda: self._move(1))
        self.list_widget.currentRowChanged.connect(self.selection_changed.emit)

    @staticmethod
    def _ghost(text: str) -> QPushButton:
        btn = QPushButton(text)
        btn.setObjectName("GhostButton")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        return btn

    def set_rules(self, rules: List[RuleItem]) -> None:
        """Replace the list (stores references owned by the document)."""
        self._rules = rules
        self._refresh_labels(keep_row=self.list_widget.currentRow())

    def rules(self) -> List[RuleItem]:
        """Return the current rule list (same objects as the document)."""
        return self._rules

    def current_index(self) -> int:
        """Return the selected rule index, or -1."""
        return self.list_widget.currentRow()

    def set_current_index(self, index: int) -> None:
        """Select a rule by index."""
        if 0 <= index < self.list_widget.count():
            self.list_widget.setCurrentRow(index)

    def refresh_current_label(self) -> None:
        """Update the label of the selected rule after an in-place edit."""
        row = self.list_widget.currentRow()
        if 0 <= row < len(self._rules):
            item = self.list_widget.item(row)
            item.setText(self._label_for(self._rules[row]))
            item.setToolTip(self._tooltip_for(self._rules[row]))

    def _label_for(self, rule: RuleItem) -> str:
        status = "● " if rule.enabled else "○ "
        return f"{status}{rule.name}"

    def _tooltip_for(self, rule: RuleItem) -> str:
        locs = ", ".join(rule.locations) if rule.locations else "(no locations)"
        return (
            f"{rule.name}\n"
            f"Targets: {rule.targets}\n"
            f"Locations: {locs}\n"
            f"Filters: {len(rule.filters)} · Actions: {len(rule.actions)}"
        )

    def _refresh_labels(self, keep_row: int = -1) -> None:
        self.list_widget.blockSignals(True)
        self.list_widget.clear()
        for rule in self._rules:
            item = QListWidgetItem(self._label_for(rule))
            item.setToolTip(self._tooltip_for(rule))
            self.list_widget.addItem(item)
        self.list_widget.blockSignals(False)
        if self._rules:
            row = keep_row if 0 <= keep_row < len(self._rules) else 0
            self.list_widget.setCurrentRow(row)
        else:
            self.selection_changed.emit(-1)

    def _add(self) -> None:
        rule = RuleItem.default_example()
        rule.name = f"Rule {len(self._rules) + 1}"
        self._rules.append(rule)
        self._refresh_labels(keep_row=len(self._rules) - 1)
        self.changed.emit()

    def _duplicate(self) -> None:
        row = self.list_widget.currentRow()
        if row < 0:
            return
        clone = self._rules[row].clone()
        clone.name = f"{clone.name} (copy)"
        self._rules.insert(row + 1, clone)
        self._refresh_labels(keep_row=row + 1)
        self.changed.emit()

    def _remove(self) -> None:
        row = self.list_widget.currentRow()
        if row < 0:
            return
        del self._rules[row]
        new_row = min(row, len(self._rules) - 1)
        self._refresh_labels(keep_row=new_row)
        self.changed.emit()

    def _move(self, delta: int) -> None:
        row = self.list_widget.currentRow()
        if row < 0:
            return
        new_row = row + delta
        if new_row < 0 or new_row >= len(self._rules):
            return
        self._rules[row], self._rules[new_row] = self._rules[new_row], self._rules[row]
        self._refresh_labels(keep_row=new_row)
        self.changed.emit()
