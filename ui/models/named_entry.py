"""Parse and emit a single YAML filter or action item."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from ui.models.item_spec import ItemSpec


@dataclass
class NamedEntry:
    """One filter or action as the visual editor understands it.

    Organize YAML accepts three shapes::

        - extension
        - extension: pdf
        - name:
            contains: Invoice
        - not empty
    """

    name: str
    value: Any = None
    inverted: bool = False

    @classmethod
    def parse(cls, item: Any) -> "NamedEntry":
        """Normalize a YAML list item into a :class:`NamedEntry`."""
        if isinstance(item, str):
            name, value = item, None
        elif isinstance(item, dict):
            if len(item) != 1:
                raise ValueError("Filter/action definition must have a single key")
            name, value = next(iter(item.items()))
        else:
            raise ValueError(f"Invalid filter/action entry: {item!r}")

        inverted = False
        if name.startswith("not "):
            inverted = True
            name = name[4:]
        return cls(name=name, value=value, inverted=inverted)

    def emit(self) -> Any:
        """Serialize back to a YAML-friendly mapping."""
        key = f"not {self.name}" if self.inverted else self.name
        if self.value is None or self.value == {} or self.value == []:
            return key
        return {key: self.value}

    @staticmethod
    def compact(
        params: Dict[str, Any],
        defaults: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Drop empty values and defaults so the YAML stays readable."""
        defaults = defaults or {}
        cleaned: Dict[str, Any] = {}
        for key, value in params.items():
            if value is None or value == "" or value == []:
                continue
            if key in defaults and value == defaults[key]:
                continue
            cleaned[key] = value
        return cleaned

    @classmethod
    def from_params(
        cls,
        spec: ItemSpec,
        params: Dict[str, Any],
        inverted: bool,
    ) -> "NamedEntry":
        """Build an entry from form values, collapsing a lone scalar field."""
        defaults = {field.key: field.default for field in spec.fields}
        cleaned = cls.compact(params, defaults)
        if isinstance(cleaned, dict) and len(cleaned) == 1:
            only_key = next(iter(cleaned))
            field = next((item for item in spec.fields if item.key == only_key), None)
            if field is not None and field.scalar:
                cleaned = cleaned[only_key]
        if cleaned == {}:
            cleaned = None
        return cls(
            name=spec.name,
            value=cleaned,
            inverted=inverted and spec.can_invert,
        )
