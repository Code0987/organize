"""Top-level organize configuration document held by the UI."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from ui.models.rule_item import RuleItem


@dataclass
class ConfigDocument:
    """In-memory config that can be loaded from / saved to YAML.

    Attributes:
        rules: Ordered list of rules.
        path: Filesystem path of the open file, if any.
        dirty: Whether unsaved edits exist.
    """

    rules: List[RuleItem] = field(default_factory=list)
    path: Optional[Path] = None
    dirty: bool = False

    def mark_dirty(self) -> None:
        """Flag the document as having unsaved changes."""
        self.dirty = True

    def mark_clean(self) -> None:
        """Clear the unsaved-changes flag."""
        self.dirty = False

    def to_config_dict(self) -> Dict[str, Any]:
        """Serialize to the top-level organize config mapping."""
        return {"rules": [rule.to_config_dict() for rule in self.rules]}

    @classmethod
    def from_config_dict(
        cls,
        raw: Dict[str, Any],
        path: Optional[Path] = None,
    ) -> "ConfigDocument":
        """Parse a raw config mapping into a document."""
        rules_raw = raw.get("rules") if raw else None
        if not rules_raw:
            rules: List[RuleItem] = []
        else:
            rules = [RuleItem.from_config_dict(r) for r in rules_raw]
        return cls(rules=rules, path=path, dirty=False)

    @classmethod
    def new_with_example(cls) -> "ConfigDocument":
        """Create a new document with one example rule."""
        return cls(rules=[RuleItem.default_example()], dirty=True)

    def clone(self) -> "ConfigDocument":
        """Deep-copy the document (path is preserved)."""
        return ConfigDocument(
            rules=[rule.clone() for rule in self.rules],
            path=self.path,
            dirty=self.dirty,
        )
