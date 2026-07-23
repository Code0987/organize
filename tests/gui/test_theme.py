"""Tests for light/dark theme support."""


from ui.styles.palette import ThemeMode, palette_for
from ui.styles.system_theme import detect_system_theme
from ui.styles.theme import apply_theme, build_stylesheet, current_theme_mode


def test_palettes_differ():
    light = palette_for(ThemeMode.LIGHT)
    dark = palette_for(ThemeMode.DARK)
    assert light.window_bg != dark.window_bg
    assert light.text != dark.text
    assert light.mode is ThemeMode.LIGHT
    assert dark.mode is ThemeMode.DARK


def test_build_stylesheet_embeds_palette_colors():
    dark = palette_for(ThemeMode.DARK)
    css = build_stylesheet(dark, sheet_scale=1.0)
    assert dark.window_bg in css
    assert dark.accent in css
    assert "#f4f6f8" not in css  # light window bg should not appear


def test_organize_theme_env_override(monkeypatch):
    monkeypatch.setenv("ORGANIZE_THEME", "dark")
    assert detect_system_theme() is ThemeMode.DARK
    monkeypatch.setenv("ORGANIZE_THEME", "light")
    assert detect_system_theme() is ThemeMode.LIGHT


def test_apply_theme_sets_app_properties(qapp=None):
    from PyQt6.QtWidgets import QApplication
    import sys

    app = QApplication.instance() or QApplication(sys.argv)
    apply_theme(app, ThemeMode.DARK)
    assert current_theme_mode(app) is ThemeMode.DARK
    assert "theme_mode" in [b.data().decode() if hasattr(b, "data") else str(b) for b in []] or app.property("theme_mode") == "dark"
    css = app.styleSheet()
    assert palette_for(ThemeMode.DARK).window_bg in css

    apply_theme(app, ThemeMode.LIGHT)
    assert current_theme_mode(app) is ThemeMode.LIGHT
    assert palette_for(ThemeMode.LIGHT).window_bg in app.styleSheet()
