"""Form-field metadata for a single filter or action parameter."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Tuple


@dataclass(frozen=True)
class FieldSpec:
    """Describe one editable parameter on a filter or action.

    Attributes:
        key: YAML / constructor argument name.
        label: Human-readable label shown in the form.
        kind: Widget type: ``text``, ``textarea``, ``int``, ``bool``,
            ``choice``, ``path``, or ``list``.
        default: Value treated as "unset" when serializing YAML.
        choices: Allowed values when ``kind`` is ``choice``.
        placeholder: Hint text for empty inputs.
        hint: Longer help shown under the field.
        scalar: If True and this is the only set field, emit a bare
            YAML scalar (``echo: hello``) instead of a mapping.
    """

    key: str
    label: str
    kind: str
    default: Any = None
    choices: Tuple[str, ...] = ()
    placeholder: str = ""
    hint: str = ""
    scalar: bool = False
