"""Schema describing a filter or action type and its editable fields."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from organize_gui.models.field_definition import FieldDefinition


@dataclass
class ItemSchema:
    """Metadata for one filter or action type available in the editor.

    Attributes:
        name: Registry name (e.g. ``extension``, ``move``).
        label: Display name for combo boxes.
        description: Short description for tooltips.
        fields: Ordered list of editable parameters.
        supports_files: Whether the item works when targeting files.
        supports_dirs: Whether the item works when targeting directories.
        standalone: Whether an action may run without locations (actions only).
    """

    name: str
    label: str
    description: str = ""
    fields: List[FieldDefinition] = field(default_factory=list)
    supports_files: bool = True
    supports_dirs: bool = True
    standalone: bool = False

    def field_names(self) -> List[str]:
        """Return the names of all defined fields."""
        return [f.name for f in self.fields]

    def get_field(self, name: str) -> FieldDefinition | None:
        """Look up a field definition by name."""
        for f in self.fields:
            if f.name == name:
                return f
        return None

    def default_params(self) -> dict:
        """Build a parameter dict filled with schema defaults."""
        params: dict = {}
        for f in self.fields:
            if f.default is not None:
                params[f.name] = f.default
            elif f.field_type == "bool":
                params[f.name] = False
            elif f.field_type == "list_str":
                params[f.name] = []
            elif f.field_type == "int":
                params[f.name] = 0
            else:
                params[f.name] = ""
        return params
