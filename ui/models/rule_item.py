"""Editable model for a single organize rule."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal

from ui.models.pipeline_item import PipelineItem


FilterMode = Literal["all", "any", "none"]
Targets = Literal["files", "dirs"]


@dataclass
class RuleItem:
    """UI-facing representation of an organize rule.

    Mirrors the options documented in organize's rules reference, but keeps
    filters/actions as editable :class:`PipelineItem` objects.
    """

    name: str = "New rule"
    enabled: bool = True
    targets: Targets = "files"
    locations: List[str] = field(default_factory=list)
    subfolders: bool = False
    filter_mode: FilterMode = "all"
    filters: List[PipelineItem] = field(default_factory=list)
    actions: List[PipelineItem] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)

    def clone(self) -> "RuleItem":
        """Return a deep copy of this rule."""
        return RuleItem(
            name=self.name,
            enabled=self.enabled,
            targets=self.targets,
            locations=list(self.locations),
            subfolders=self.subfolders,
            filter_mode=self.filter_mode,
            filters=[item.clone() for item in self.filters],
            actions=[item.clone() for item in self.actions],
            tags=list(self.tags),
        )

    def to_config_dict(self) -> Dict[str, Any]:
        """Serialize to the dict form organize expects under ``rules:``."""
        data: Dict[str, Any] = {
            "name": self.name,
            "enabled": self.enabled,
            "targets": self.targets,
            "locations": list(self.locations),
            "subfolders": self.subfolders,
            "filter_mode": self.filter_mode,
            "filters": [item.to_config_dict() for item in self.filters],
            "actions": [item.to_config_dict() for item in self.actions],
        }
        if self.tags:
            data["tags"] = list(self.tags)
        return data

    @classmethod
    def from_config_dict(cls, raw: Dict[str, Any]) -> "RuleItem":
        """Build a :class:`RuleItem` from a parsed YAML rule mapping."""
        locations = raw.get("locations") or []
        if isinstance(locations, str):
            locations = [locations]
        else:
            normalized: List[str] = []
            for loc in locations:
                if isinstance(loc, str):
                    normalized.append(loc)
                elif isinstance(loc, dict) and "path" in loc:
                    path = loc["path"]
                    if isinstance(path, list):
                        normalized.extend(str(p) for p in path)
                    else:
                        normalized.append(str(path))
                else:
                    normalized.append(str(loc))
            locations = normalized

        filters_raw = raw.get("filters") or []
        actions_raw = raw.get("actions") or []
        tags = raw.get("tags") or []
        if isinstance(tags, str):
            tags = [tags]

        return cls(
            name=str(raw.get("name") or "Unnamed rule"),
            enabled=bool(raw.get("enabled", True)),
            targets=raw.get("targets") or "files",
            locations=list(locations),
            subfolders=bool(raw.get("subfolders", False)),
            filter_mode=raw.get("filter_mode") or "all",
            filters=[PipelineItem.from_config_dict("filter", f) for f in filters_raw],
            actions=[PipelineItem.from_config_dict("action", a) for a in actions_raw],
            tags=[str(t) for t in tags],
        )

    @classmethod
    def default_example(cls) -> "RuleItem":
        """Create a sensible starter rule for new configs."""
        return cls(
            name="Find PDFs",
            locations=["~/Downloads"],
            subfolders=True,
            filters=[
                PipelineItem(kind="filter", name="extension", primary_value="pdf"),
            ],
            actions=[
                PipelineItem(
                    kind="action",
                    name="echo",
                    primary_value="Found PDF: {path.name}",
                ),
            ],
        )
