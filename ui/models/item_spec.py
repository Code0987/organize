"""Metadata describing one organize filter or action."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from ui.models.field_spec import FieldSpec


@dataclass(frozen=True)
class ItemSpec:
    """Schema used to render an interactive filter or action editor.

    Attributes:
        name: Registry name (``extension``, ``move``, ...).
        title: Short label for combo boxes.
        summary: One-line explanation shown in the editor.
        fields: Editable parameters.
        files: Whether the item supports file targets.
        dirs: Whether the item supports directory targets.
        standalone: Whether the action can run without locations.
        can_invert: Whether the filter may be prefixed with ``not``.
    """

    name: str
    title: str
    summary: str
    fields: Tuple[FieldSpec, ...] = ()
    files: bool = True
    dirs: bool = True
    standalone: bool = False
    can_invert: bool = False
