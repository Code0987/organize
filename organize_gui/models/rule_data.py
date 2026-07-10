"""Data model for a single organize rule."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Set

from organize_gui.models.action_data import ActionData
from organize_gui.models.filter_data import FilterData
from organize_gui.models.location_data import LocationData

FilterMode = Literal["all", "any", "none"]
Targets = Literal["files", "dirs"]


@dataclass
class RuleData:
    """Editable representation of one organize rule.

    Attributes:
        name: Optional human-readable rule name.
        enabled: Whether the rule is active.
        targets: Whether to process files or directories.
        locations: Search locations.
        subfolders: Whether to recurse into subfolders.
        tags: Tags used to selectively run rules.
        filters: Filters applied to each resource.
        filter_mode: How filters combine (all / any / none).
        actions: Actions executed for matching resources.
    """

    name: str = ""
    enabled: bool = True
    targets: Targets = "files"
    locations: List[LocationData] = field(default_factory=list)
    subfolders: bool = False
    tags: Set[str] = field(default_factory=set)
    filters: List[FilterData] = field(default_factory=list)
    filter_mode: FilterMode = "all"
    actions: List[ActionData] = field(default_factory=list)

    def display_label(self) -> str:
        """Return a short label for the rule list."""
        status = "" if self.enabled else "[disabled] "
        if self.name:
            return f"{status}{self.name}"
        if self.locations:
            loc = self.locations[0].display_label()
            return f"{status}(unnamed) — {loc}"
        return f"{status}(unnamed rule)"

    def to_yaml_dict(self) -> Dict[str, Any]:
        """Serialize this rule to a mapping for YAML output."""
        data: Dict[str, Any] = {}
        if self.name:
            data["name"] = self.name
        if not self.enabled:
            data["enabled"] = False
        if self.targets != "files":
            data["targets"] = self.targets

        if len(self.locations) == 1 and self.locations[0].is_simple():
            data["locations"] = self.locations[0].path[0]
        else:
            data["locations"] = [loc.to_yaml_value() for loc in self.locations]

        if self.subfolders:
            data["subfolders"] = True
        if self.tags:
            data["tags"] = sorted(self.tags)
        if self.filter_mode != "all":
            data["filter_mode"] = self.filter_mode
        if self.filters:
            data["filters"] = [f.to_yaml_value() for f in self.filters]
        data["actions"] = [a.to_yaml_value() for a in self.actions]
        return data

    @classmethod
    def from_yaml_dict(cls, data: Dict[str, Any]) -> "RuleData":
        """Parse a YAML rule mapping into a :class:`RuleData`."""
        if not isinstance(data, dict):
            raise ValueError("Rule must be a mapping")

        name = str(data.get("name") or "")
        enabled = bool(data.get("enabled", True))
        targets = data.get("targets", "files")
        if targets not in ("files", "dirs"):
            targets = "files"

        locations_raw = data.get("locations")
        locations: List[LocationData] = []
        if locations_raw is None:
            locations = []
        elif isinstance(locations_raw, (str, dict)):
            locations = [LocationData.from_yaml_value(locations_raw)]
        elif isinstance(locations_raw, list):
            locations = [LocationData.from_yaml_value(x) for x in locations_raw]

        subfolders = bool(data.get("subfolders", False))
        tags_raw = data.get("tags") or []
        if isinstance(tags_raw, str):
            tags = {tags_raw}
        else:
            tags = {str(t) for t in tags_raw}

        filter_mode = data.get("filter_mode", "all")
        if filter_mode not in ("all", "any", "none"):
            filter_mode = "all"

        filters_raw = data.get("filters") or []
        if not isinstance(filters_raw, list):
            filters_raw = [filters_raw]
        filters = [FilterData.from_yaml_value(x) for x in filters_raw]

        actions_raw = data.get("actions") or []
        if not isinstance(actions_raw, list):
            actions_raw = [actions_raw]
        actions = [ActionData.from_yaml_value(x) for x in actions_raw]

        return cls(
            name=name,
            enabled=enabled,
            targets=targets,  # type: ignore[arg-type]
            locations=locations,
            subfolders=subfolders,
            tags=tags,
            filters=filters,
            filter_mode=filter_mode,  # type: ignore[arg-type]
            actions=actions,
        )

    @classmethod
    def create_default(cls) -> "RuleData":
        """Create a sensible starter rule for the editor."""
        return cls(
            name="New rule",
            enabled=True,
            targets="files",
            locations=[LocationData(path=["~/Downloads"])],
            subfolders=False,
            tags=set(),
            filters=[FilterData.create_default("extension")],
            filter_mode="all",
            actions=[ActionData.create_default("echo")],
        )
