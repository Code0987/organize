"""Field metadata used to generate interactive filter/action forms."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Literal, Optional, Sequence


FieldType = Literal[
    "str",
    "int",
    "float",
    "bool",
    "choice",
    "list_str",
    "multiline",
]


@dataclass(frozen=True)
class FieldSpec:
    """Describes one editable parameter on a filter or action form.

    Attributes:
        name: Parameter key written into YAML.
        label: Human-friendly label shown in the form.
        field_type: Widget type to render.
        required: Whether the field must be filled for a valid item.
        default: Default value when creating a new item.
        choices: Allowed values for ``choice`` fields.
        help_text: Short helper text shown under the control.
        is_primary: If True and this is the only meaningful value, the
            UI may serialize the item in shorthand form
            (e.g. ``extension: pdf`` instead of ``extension: {extensions: …}``).
        primary_aliases: Alternative keys used when loading shorthand YAML
            into structured params.
    """

    name: str
    label: str
    field_type: FieldType = "str"
    required: bool = False
    default: Any = None
    choices: Sequence[str] = field(default_factory=tuple)
    help_text: str = ""
    is_primary: bool = False
    primary_aliases: Sequence[str] = field(default_factory=tuple)


@dataclass(frozen=True)
class ItemSchema:
    """Schema for one filter or action type.

    Attributes:
        name: Registry name (``extension``, ``move``, …).
        label: Title shown in the type picker.
        description: One-line description of the filter/action.
        fields: Ordered form fields.
        allow_empty: Whether the item is valid with no parameters
            (e.g. ``empty``, ``delete``, ``trash``).
        supports_invert: Whether filters may use the ``not`` prefix.
    """

    name: str
    label: str
    description: str
    fields: Sequence[FieldSpec] = field(default_factory=tuple)
    allow_empty: bool = False
    supports_invert: bool = True

    def defaults(self) -> Dict[str, Any]:
        """Return a dict of default parameter values."""
        result: Dict[str, Any] = {}
        for spec in self.fields:
            if spec.default is not None:
                result[spec.name] = spec.default
        return result

    def primary_field(self) -> Optional[FieldSpec]:
        """Return the field marked as primary, if any."""
        for spec in self.fields:
            if spec.is_primary:
                return spec
        return None
