"""In-memory document model for a full organize config file."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from organize_gui.models.rule_data import RuleData


@dataclass
class ConfigDocument:
    """Represents an organize configuration (list of rules) being edited.

    Attributes:
        rules: Ordered list of rules.
        source_path: Path the document was loaded from, if any.
        dirty: Whether the document has unsaved changes.
    """

    rules: List[RuleData] = field(default_factory=list)
    source_path: Optional[Path] = None
    dirty: bool = False

    def mark_dirty(self) -> None:
        """Flag the document as having unsaved changes."""
        self.dirty = True

    def mark_clean(self) -> None:
        """Flag the document as saved / clean."""
        self.dirty = False

    def to_yaml_dict(self) -> Dict[str, Any]:
        """Serialize the full config to a mapping for YAML output."""
        return {"rules": [rule.to_yaml_dict() for rule in self.rules]}

    @classmethod
    def from_yaml_dict(
        cls,
        data: Any,
        source_path: Optional[Path] = None,
    ) -> "ConfigDocument":
        """Parse a YAML root mapping into a :class:`ConfigDocument`."""
        if data is None:
            return cls(rules=[], source_path=source_path)
        if not isinstance(data, dict):
            raise ValueError("Config root must be a mapping with a 'rules' key")
        rules_raw = data.get("rules")
        if rules_raw is None:
            rules_raw = []
        if not isinstance(rules_raw, list):
            raise ValueError("'rules' must be a list")
        rules = [RuleData.from_yaml_dict(r) for r in rules_raw]
        return cls(rules=rules, source_path=source_path, dirty=False)

    @classmethod
    def create_empty(cls) -> "ConfigDocument":
        """Create a new empty document with one starter rule."""
        doc = cls(rules=[RuleData.create_default()], dirty=True)
        return doc

    def display_title(self) -> str:
        """Return a window title fragment for this document."""
        name = self.source_path.name if self.source_path else "Untitled"
        marker = " *" if self.dirty else ""
        return f"{name}{marker}"
