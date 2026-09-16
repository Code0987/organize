"""Selectable list of rules in the current config."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QListWidget, QListWidgetItem, QWidget

from ui.models.rule_summary import RuleSummary


class RuleList(QListWidget):
    """Shows rule names and a summary tooltip for each rule."""

    rule_selected = pyqtSignal(int)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._summary = RuleSummary()
        self.currentRowChanged.connect(self.rule_selected.emit)

    def set_rules(self, rules: List[Dict[str, Any]], selected: int = -1) -> None:
        """Rebuild the list without emitting a selection change storm."""
        blocked = self.blockSignals(True)
        self.clear()
        for rule in rules:
            name = str(rule.get("name") or "Untitled rule")
            if rule.get("enabled", True) is False:
                name = f"⊘  {name}"
            item = QListWidgetItem(name)
            item.setToolTip(self._summary.summarize(rule))
            self.addItem(item)
        if 0 <= selected < len(rules):
            self.setCurrentRow(selected)
        self.blockSignals(blocked)
        if 0 <= selected < len(rules):
            self.rule_selected.emit(selected)
