"""Data model for a single rule action entry."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict

from organize_gui.models.action_schemas import get_action_schema
from organize_gui.models.filter_data import parse_list_str_value


@dataclass
class ActionData:
    """Editable representation of one action in a rule.

    Attributes:
        name: Action type name (e.g. ``move``, ``echo``).
        params: Mapping of parameter names to values.
    """

    name: str = "echo"
    params: Dict[str, Any] = field(default_factory=dict)

    def display_label(self) -> str:
        """Return a short label for list widgets."""
        schema = get_action_schema(self.name)
        summary = self._param_summary()
        if summary:
            return f"{schema.label}: {summary}"
        return schema.label

    def _param_summary(self) -> str:
        """Build a brief one-line summary of the parameters."""
        if not self.params:
            return ""
        schema = get_action_schema(self.name)
        primary = next((f for f in schema.fields if f.is_primary), None)
        if primary and primary.name in self.params:
            val = self.params[primary.name]
            if isinstance(val, list):
                return ", ".join(str(v) for v in val[:3])
            text = str(val)
            return text if len(text) <= 40 else text[:37] + "…"
        for key, val in self.params.items():
            if val in (None, "", [], {}, 0, False):
                continue
            text = str(val)
            return f"{key}={text[:30]}"
        return ""

    def to_yaml_value(self) -> Any:
        """Serialize to a YAML list item (string or single-key mapping)."""
        key = self.name
        schema = get_action_schema(self.name)
        cleaned = self._cleaned_params(schema)

        if not cleaned:
            return key

        primary_fields = [f for f in schema.fields if f.is_primary]
        if len(cleaned) == 1 and primary_fields:
            p = primary_fields[0]
            if p.name in cleaned:
                return {key: cleaned[p.name]}

        return {key: cleaned}

    def _cleaned_params(self, schema) -> Dict[str, Any]:
        """Drop empty / default-equivalent values for cleaner YAML."""
        result: Dict[str, Any] = {}
        for fdef in schema.fields:
            if fdef.name not in self.params:
                continue
            val = self.params[fdef.name]
            if val is None:
                continue
            if fdef.field_type == "list_str" and val == []:
                continue
            if fdef.field_type in ("str", "text", "path") and val == "" and not fdef.required:
                continue
            if (
                not fdef.required
                and fdef.default is not None
                and val == fdef.default
                and not fdef.is_primary
            ):
                continue
            result[fdef.name] = val
        known = set(schema.field_names())
        for k, v in self.params.items():
            if k not in known and k != "value":
                result[k] = v
        return result

    @classmethod
    def from_yaml_value(cls, value: Any) -> "ActionData":
        """Parse a YAML action list item into an :class:`ActionData`."""
        if value is None:
            return cls()
        if isinstance(value, str):
            name = value
            schema = get_action_schema(name)
            return cls(name=name, params=schema.default_params())

        if isinstance(value, dict):
            if not value:
                return cls()
            name, raw = next(iter(value.items()))
            name = str(name)
            schema = get_action_schema(name)
            params = schema.default_params()
            params.update(cls._parse_raw_params(schema, raw))
            return cls(name=name, params=params)

        return cls()

    @staticmethod
    def _parse_raw_params(schema, raw: Any) -> Dict[str, Any]:
        """Normalize a YAML action value into a params dict."""
        if raw is None:
            return {}
        if isinstance(raw, dict):
            return dict(raw)

        primary = next((f for f in schema.fields if f.is_primary), None)
        if primary is None and schema.fields:
            primary = schema.fields[0]
        if primary is None:
            return {"value": raw}

        if primary.field_type == "list_str":
            return {primary.name: parse_list_str_value(primary.name, raw)}

        return {primary.name: raw}

    @classmethod
    def create_default(cls, name: str = "echo") -> "ActionData":
        """Create a new action with schema defaults."""
        schema = get_action_schema(name)
        return cls(name=name, params=schema.default_params())
