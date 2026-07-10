"""Field definition used to drive dynamic form widgets."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List, Optional


@dataclass
class FieldDefinition:
    """Describes a single configurable parameter for a filter or action.

    Attributes:
        name: Internal parameter name matching the organize filter/action field.
        label: Human-readable label shown in the form.
        field_type: Widget type: ``str``, ``int``, ``bool``, ``choice``,
            ``list_str``, ``path``, ``text``.
        required: Whether the field must be provided.
        default: Default value used when creating a new item.
        choices: Valid options when ``field_type`` is ``choice``.
        help_text: Optional short help shown as a tooltip.
        is_primary: If True, a lone value may be serialized as the filter/action
            value itself (YAML shorthand) instead of a nested mapping.
    """

    name: str
    label: str
    field_type: str
    required: bool = False
    default: Any = None
    choices: Optional[List[str]] = None
    help_text: str = ""
    is_primary: bool = False
