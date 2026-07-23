"""Visual styling for the organize desktop GUI."""

from ui.styles.combo_fix import configure_combobox, polish_comboboxes
from ui.styles.dpi import configure_process_dpi, effective_ui_scale, screen_scale_factor, sp
from ui.styles.palette import ColorPalette, ThemeMode, palette_for
from ui.styles.system_theme import ThemeWatcher, detect_system_theme
from ui.styles.theme import (
    apply_theme,
    current_palette,
    current_theme_mode,
    ui_scale,
)

__all__ = [
    "ColorPalette",
    "ThemeMode",
    "ThemeWatcher",
    "apply_theme",
    "configure_combobox",
    "configure_process_dpi",
    "current_palette",
    "current_theme_mode",
    "detect_system_theme",
    "effective_ui_scale",
    "palette_for",
    "polish_comboboxes",
    "screen_scale_factor",
    "sp",
    "ui_scale",
]
