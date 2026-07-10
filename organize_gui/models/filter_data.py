"""Data model for a single rule filter entry."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from organize_gui.models.filter_schemas import get_filter_schema

# Fields where a bare string is conventionally space-separated tokens
# (e.g. extension: "pdf jpg"). Other list_str fields keep a single string
# so values like size ">= 500 MB" are not broken apart.
_SPACE_SPLIT_LIST_FIELDS = frozenset({"extensions", "mimetypes", "tags"})


def parse_list_str_value(field_name: str, raw: Any) -> List[str]:
    """Normalize a YAML scalar/list into a list of strings for ``list_str`` fields.

    Rules:
    - lists are stringified element-wise
    - comma-separated strings always split on commas
    - space-separated splitting is only applied for multi-token fields such as
      extensions; otherwise the whole string is kept as one entry
    """
    if isinstance(raw, list):
        return [str(x) for x in raw]
    if not isinstance(raw, str):
        return [str(raw)]
    text = raw.strip()
    if not text:
        return []
    if "," in text:
        return [p.strip() for p in text.split(",") if p.strip()]
    if field_name in _SPACE_SPLIT_LIST_FIELDS:
        return [p.strip() for p in text.split() if p.strip()]
    return [text]


@dataclass
class FilterData:
    """Editable representation of one filter in a rule.

    Attributes:
        name: Filter type name (e.g. ``extension``, ``name``).
        params: Mapping of parameter names to values.
        inverted: If True, the filter is prefixed with ``not`` in YAML.
    """

    name: str = "extension"
    params: Dict[str, Any] = field(default_factory=dict)
    inverted: bool = False

    def display_label(self) -> str:
        """Return a short label for list widgets."""
        prefix = "not " if self.inverted else ""
        schema = get_filter_schema(self.name)
        summary = self._param_summary()
        if summary:
            return f"{prefix}{schema.label}: {summary}"
        return f"{prefix}{schema.label}"

    def _param_summary(self) -> str:
        """Build a brief one-line summary of the parameters."""
        if not self.params:
            return ""
        schema = get_filter_schema(self.name)
        primary = next((f for f in schema.fields if f.is_primary), None)
        if primary and primary.name in self.params:
            val = self.params[primary.name]
            if isinstance(val, list):
                return ", ".join(str(v) for v in val[:3]) + (
                    "…" if len(val) > 3 else ""
                )
            text = str(val)
            return text if len(text) <= 40 else text[:37] + "…"
        # Show first non-empty param
        for key, val in self.params.items():
            if val in (None, "", [], {}, 0, False):
                continue
            if isinstance(val, list):
                return f"{key}={','.join(str(v) for v in val[:2])}"
            text = str(val)
            return f"{key}={text[:30]}"
        return ""

    def to_yaml_value(self) -> Any:
        """Serialize to a YAML list item (string or single-key mapping)."""
        key = f"not {self.name}" if self.inverted else self.name
        schema = get_filter_schema(self.name)
        cleaned = self._cleaned_params(schema)

        if not cleaned:
            return key

        # Shorthand: single primary field -> {name: value}
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
            if fdef.field_type in ("str", "text") and val == "" and not fdef.required:
                continue
            # Skip values equal to schema default for optional non-primary fields
            if (
                not fdef.required
                and fdef.default is not None
                and val == fdef.default
                and not fdef.is_primary
            ):
                continue
            result[fdef.name] = val
        # Keep unknown keys for forward compatibility
        known = set(schema.field_names())
        for k, v in self.params.items():
            if k not in known:
                result[k] = v
        return result

    @classmethod
    def from_yaml_value(cls, value: Any) -> "FilterData":
        """Parse a YAML filter list item into a :class:`FilterData`."""
        if value is None:
            return cls()
        if isinstance(value, str):
            name = value
            inverted = False
            if name.startswith("not "):
                inverted = True
                name = name[4:]
            schema = get_filter_schema(name)
            return cls(name=name, params=schema.default_params(), inverted=inverted)

        if isinstance(value, dict):
            if len(value) != 1:
                # Unexpected multi-key; take first
                if not value:
                    return cls()
            name, raw = next(iter(value.items()))
            inverted = False
            if isinstance(name, str) and name.startswith("not "):
                inverted = True
                name = name[4:]
            name = str(name)
            schema = get_filter_schema(name)
            params = schema.default_params()
            params.update(cls._parse_raw_params(schema, raw))
            return cls(name=name, params=params, inverted=inverted)

        return cls()

    @staticmethod
    def _parse_raw_params(schema, raw: Any) -> Dict[str, Any]:
        """Normalize a YAML filter value into a params dict."""
        if raw is None:
            return {}
        if isinstance(raw, dict):
            return dict(raw)

        # Scalar / list assigned to primary field
        primary = next((f for f in schema.fields if f.is_primary), None)
        if primary is None and schema.fields:
            primary = schema.fields[0]
        if primary is None:
            return {"value": raw}

        if primary.field_type == "list_str":
            return {primary.name: parse_list_str_value(primary.name, raw)}

        return {primary.name: raw}

    @classmethod
    def create_default(cls, name: str = "extension") -> "FilterData":
        """Create a new filter with schema defaults."""
        schema = get_filter_schema(name)
        return cls(name=name, params=schema.default_params(), inverted=False)
