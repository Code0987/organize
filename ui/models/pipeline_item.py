"""A single filter or action entry in a rule pipeline."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any, Dict, Literal, Optional


ItemKind = Literal["filter", "action"]


@dataclass
class PipelineItem:
    """Editable representation of one filter or action.

    Attributes:
        kind: Whether this item is a filter or an action.
        name: Registry name (e.g. ``extension``, ``move``).
        params: Keyword arguments for the filter/action.
        inverted: For filters only — when True, the name is emitted as
            ``"not <name>"`` in YAML (organize's exclude syntax).
        primary_value: Optional shorthand value used when a filter/action
            accepts a single positional-style config value
            (e.g. ``extension: pdf``).
    """

    kind: ItemKind
    name: str
    params: Dict[str, Any] = field(default_factory=dict)
    inverted: bool = False
    primary_value: Optional[Any] = None

    def clone(self) -> "PipelineItem":
        """Return a deep copy of this item."""
        return PipelineItem(
            kind=self.kind,
            name=self.name,
            params=deepcopy(self.params),
            inverted=self.inverted,
            primary_value=deepcopy(self.primary_value),
        )

    def display_label(self) -> str:
        """Human-readable one-line summary for list widgets."""
        prefix = "not " if self.inverted and self.kind == "filter" else ""
        if self.params:
            # Compact preview of a few params.
            bits = []
            for key, value in list(self.params.items())[:3]:
                bits.append(f"{key}={value!r}")
            if len(self.params) > 3:
                bits.append("…")
            return f"{prefix}{self.name}: {', '.join(bits)}"
        if self.primary_value is not None:
            return f"{prefix}{self.name}: {self.primary_value!r}"
        return f"{prefix}{self.name}"

    def to_config_dict(self) -> Dict[str, Any]:
        """Serialize to the dict form organize expects in YAML."""
        key = f"not {self.name}" if self.inverted and self.kind == "filter" else self.name
        if self.params:
            return {key: deepcopy(self.params)}
        if self.primary_value is not None:
            return {key: deepcopy(self.primary_value)}
        return {key: None}

    @classmethod
    def from_config_dict(cls, kind: ItemKind, raw: Any) -> "PipelineItem":
        """Parse a YAML filter/action entry into a :class:`PipelineItem`."""
        if isinstance(raw, str):
            name = raw
            inverted = False
            if kind == "filter" and name.startswith("not "):
                inverted = True
                name = name[4:]
            return cls(kind=kind, name=name, inverted=inverted)

        if not isinstance(raw, dict) or len(raw) != 1:
            raise ValueError(f"Invalid {kind} entry: {raw!r}")

        key, value = next(iter(raw.items()))
        inverted = False
        name = str(key)
        if kind == "filter" and name.startswith("not "):
            inverted = True
            name = name[4:]

        if value is None:
            return cls(kind=kind, name=name, inverted=inverted)
        if isinstance(value, dict):
            return cls(kind=kind, name=name, params=dict(value), inverted=inverted)
        return cls(kind=kind, name=name, primary_value=value, inverted=inverted)
