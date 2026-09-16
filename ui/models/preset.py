"""A starter organize config the user can clone."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Preset:
    """Built-in YAML template offered by the New Config dialog.

    Attributes:
        id: Stable identifier used in tests and settings.
        title: Short name shown in the dialog.
        description: What the preset does.
        yaml: Full organize configuration text.
        builtin: Always True for shipped presets.
    """

    id: str
    title: str
    description: str
    yaml: str
    builtin: bool = True
