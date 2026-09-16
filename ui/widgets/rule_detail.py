"""Form for the currently selected rule."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QFormLayout,
    QGroupBox,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from ui.widgets.location_editor import LocationEditor
from ui.widgets.named_item_editor import NamedItemEditor
from ui.widgets.scroll_combo_box import ScrollComboBox


class RuleDetail(QWidget):
    """Interactive editor for name, locations, filters, and actions."""

    changed = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._loading = False
        self.filter_editors: List[NamedItemEditor] = []
        self.action_editors: List[NamedItemEditor] = []

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        inner = QWidget()
        self.body = QVBoxLayout(inner)
        self.body.setContentsMargins(4, 4, 4, 4)

        form = QFormLayout()
        self.name = QLineEdit()
        self.enabled = QCheckBox("Enabled")
        self.enabled.setChecked(True)
        self.targets = ScrollComboBox()
        self.targets.addItems(["files", "dirs"])
        self.subfolders = QCheckBox("Include subfolders")
        self.filter_mode = ScrollComboBox()
        self.filter_mode.addItems(["all", "any", "none"])
        self.tags = QLineEdit()
        self.tags.setPlaceholderText("comma,separated,tags")
        form.addRow("Name", self.name)
        form.addRow("", self.enabled)
        form.addRow("Targets", self.targets)
        form.addRow("", self.subfolders)
        form.addRow("Filter mode", self.filter_mode)
        form.addRow("Tags", self.tags)
        self.body.addLayout(form)

        self.name.textChanged.connect(lambda _text: self._emit())
        self.tags.textChanged.connect(lambda _text: self._emit())
        self.enabled.stateChanged.connect(lambda _value: self._emit())
        self.subfolders.stateChanged.connect(lambda _value: self._emit())
        self.targets.currentTextChanged.connect(lambda _text: self._emit())
        self.filter_mode.currentTextChanged.connect(lambda _text: self._emit())

        self.locations = LocationEditor()
        self.locations.changed.connect(self._emit)
        self.body.addWidget(self.locations)

        self.filters_host = QVBoxLayout()
        self.body.addWidget(self._named_group("Filters", self.filters_host, "filter"))
        self.actions_host = QVBoxLayout()
        self.body.addWidget(self._named_group("Actions", self.actions_host, "action"))
        self.body.addStretch(1)
        scroll.setWidget(inner)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(scroll)

    def _named_group(self, title: str, host: QVBoxLayout, kind: str) -> QGroupBox:
        box = QGroupBox(title)
        layout = QVBoxLayout(box)
        layout.addLayout(host)
        add = QPushButton(f"Add {kind}")
        add.clicked.connect(lambda: self._add_named(kind))
        layout.addWidget(add, alignment=Qt.AlignmentFlag.AlignLeft)
        return box

    def _add_named(self, kind: str, entry: Any = None) -> NamedItemEditor:
        editor = NamedItemEditor(kind)
        if entry is not None:
            editor.set_entry(entry)
        editor.changed.connect(self._emit)
        host = self.filters_host if kind == "filter" else self.actions_host
        collection = self.filter_editors if kind == "filter" else self.action_editors

        def _remove() -> None:
            collection.remove(editor)
            editor.setParent(None)
            editor.deleteLater()
            self._emit()

        editor.remove_requested.connect(_remove)
        host.addWidget(editor)
        collection.append(editor)
        self._emit()
        return editor

    def _clear_named(self) -> None:
        for editor in self.filter_editors + self.action_editors:
            editor.setParent(None)
            editor.deleteLater()
        self.filter_editors.clear()
        self.action_editors.clear()

    def load_rule(self, rule: Dict[str, Any]) -> None:
        """Populate the form from a rule mapping."""
        self._loading = True
        self.name.setText(str(rule.get("name") or ""))
        self.enabled.setChecked(bool(rule.get("enabled", True)))
        self.targets.setCurrentText(str(rule.get("targets") or "files"))
        self.subfolders.setChecked(bool(rule.get("subfolders", False)))
        self.filter_mode.setCurrentText(str(rule.get("filter_mode") or "all"))
        tags = rule.get("tags") or []
        if isinstance(tags, (list, set, tuple)):
            self.tags.setText(", ".join(str(tag) for tag in tags))
        else:
            self.tags.setText(str(tags))

        paths: List[str] = []
        locations = rule.get("locations") or []
        if isinstance(locations, str):
            locations = [locations]
        for location in locations:
            if isinstance(location, dict):
                path = location.get("path", "")
                if isinstance(path, list):
                    paths.extend(str(item) for item in path)
                elif path:
                    paths.append(str(path))
            elif location:
                paths.append(str(location))
        self.locations.set_paths(paths)

        self._clear_named()
        for entry in rule.get("filters") or []:
            self._add_named("filter", entry)
        for entry in rule.get("actions") or []:
            self._add_named("action", entry)
        self._loading = False

    def to_rule(self) -> Dict[str, Any]:
        """Serialize the form to an organize rule mapping."""
        tags = [tag.strip() for tag in self.tags.text().split(",") if tag.strip()]
        rule: Dict[str, Any] = {
            "name": self.name.text().strip() or "Untitled rule",
            "enabled": self.enabled.isChecked(),
            "targets": self.targets.currentText(),
            "locations": self.locations.paths(),
            "subfolders": self.subfolders.isChecked(),
            "filter_mode": self.filter_mode.currentText(),
            "filters": [editor.to_entry() for editor in self.filter_editors],
            "actions": [editor.to_entry() for editor in self.action_editors],
        }
        if tags:
            rule["tags"] = tags
        return rule

    def _emit(self) -> None:
        if not self._loading:
            self.changed.emit()
