"""Color palettes for light and dark UI themes."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Dict


class ThemeMode(str, Enum):
    """Supported appearance modes."""

    LIGHT = "light"
    DARK = "dark"


@dataclass(frozen=True)
class ColorPalette:
    """Semantic colors used to build the application stylesheet."""

    mode: ThemeMode

    # Surfaces
    window_bg: str
    panel_bg: str
    card_bg: str
    input_bg: str
    muted_bg: str
    hover_bg: str
    selected_bg: str

    # Text
    text: str
    text_muted: str
    text_faint: str
    text_on_accent: str

    # Borders / lines
    border: str
    border_strong: str
    focus_border: str

    # Accents / status
    accent: str
    accent_hover: str
    danger_bg: str
    danger_text: str
    danger_border: str
    selection_bg: str

    # Activity / code panels
    log_bg: str
    log_text: str
    log_border: str
    code_bg: str
    code_text: str
    code_border: str

    # Tooltip
    tooltip_bg: str
    tooltip_text: str

    def as_map(self) -> Dict[str, str]:
        """Return token name → color for stylesheet formatting."""
        data = asdict(self)
        data["mode"] = self.mode.value
        return data


LIGHT_PALETTE = ColorPalette(
    mode=ThemeMode.LIGHT,
    window_bg="#f4f6f8",
    panel_bg="#ffffff",
    card_bg="#fafbfc",
    input_bg="#ffffff",
    muted_bg="#f5f7fa",
    hover_bg="#eef2f7",
    selected_bg="#e8f1ff",
    text="#1f2933",
    text_muted="#52606d",
    text_faint="#7b8794",
    text_on_accent="#ffffff",
    border="#e5e9ef",
    border_strong="#d9e2ec",
    focus_border="#0b5fff",
    accent="#0b5fff",
    accent_hover="#0047d4",
    danger_bg="#fff5f5",
    danger_text="#b00020",
    danger_border="#f5c2c7",
    selection_bg="#cfe0ff",
    log_bg="#0f1720",
    log_text="#d9e2ec",
    log_border="#243b53",
    code_bg="#fafbfc",
    code_text="#1f2933",
    code_border="#e5e9ef",
    tooltip_bg="#323f4b",
    tooltip_text="#ffffff",
)


DARK_PALETTE = ColorPalette(
    mode=ThemeMode.DARK,
    window_bg="#0f1419",
    panel_bg="#171c22",
    card_bg="#1c232b",
    input_bg="#12171d",
    muted_bg="#1c232b",
    hover_bg="#243040",
    selected_bg="#1a2f4a",
    text="#e7ecf1",
    text_muted="#a7b3c0",
    text_faint="#7f8b99",
    text_on_accent="#ffffff",
    border="#2a3441",
    border_strong="#3a4656",
    focus_border="#4c8dff",
    accent="#4c8dff",
    accent_hover="#6aa1ff",
    danger_bg="#3a1717",
    danger_text="#ff8e8e",
    danger_border="#6b2c2c",
    selection_bg="#26456e",
    log_bg="#0a0e13",
    log_text="#d9e2ec",
    log_border="#2a3441",
    code_bg="#12171d",
    code_text="#e7ecf1",
    code_border="#2a3441",
    tooltip_bg="#e7ecf1",
    tooltip_text="#0f1419",
)


def palette_for(mode: ThemeMode) -> ColorPalette:
    """Return the palette for *mode*."""
    return DARK_PALETTE if mode is ThemeMode.DARK else LIGHT_PALETTE
