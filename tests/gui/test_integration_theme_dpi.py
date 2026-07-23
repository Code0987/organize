"""Integration tests for theme + DPI working together."""

from __future__ import annotations


import pytest

from ui.styles.dpi import screen_scale_factor, sp
from ui.styles.palette import ThemeMode, palette_for
from ui.styles.system_theme import detect_system_theme
from ui.styles.theme import apply_theme, build_stylesheet, current_palette, current_theme_mode


pytestmark = pytest.mark.usefixtures("qapp")


def test_detect_system_theme_respects_env(monkeypatch):
    monkeypatch.setenv("ORGANIZE_THEME", "dark")
    assert detect_system_theme() is ThemeMode.DARK
    monkeypatch.setenv("ORGANIZE_THEME", "light")
    assert detect_system_theme() is ThemeMode.LIGHT


def test_apply_both_themes_produce_opaque_window_styles(qapp):
    for mode in (ThemeMode.LIGHT, ThemeMode.DARK):
        apply_theme(qapp, mode)
        css = " ".join(qapp.styleSheet().split())
        palette = palette_for(mode)
        assert palette.window_bg in qapp.styleSheet()
        assert "QMainWindow" in css
        # Structural surfaces are filled
        assert "QFrame#SidePanel" in css
        assert "QScrollArea" in css
        # Regression: global transparent QWidget background
        assert "QWidget { background: transparent" not in css
        assert "QWidget { background-color: transparent" not in css
        assert current_theme_mode(qapp) is mode
        assert current_palette(qapp).mode is mode


def test_stylesheet_scaling_composes_with_theme():
    dark = palette_for(ThemeMode.DARK)
    scaled = build_stylesheet(dark, sheet_scale=1.5)
    # 12px design token → 18px at 1.5x
    assert "18px" in scaled or sp(12, 1.5) == 18
    assert dark.window_bg in scaled
    # unscaled baseline still has design 12px for log font
    base = build_stylesheet(dark, sheet_scale=1.0)
    assert "12px" in base


def test_screen_scale_factor_is_one_when_qt_scale_injected(qapp, monkeypatch):
    # With ORGANIZE_UI_SCALE set in conftest, stylesheet scale should be 1.0
    # to avoid double-scaling.
    factor = screen_scale_factor(qapp)
    assert factor == pytest.approx(1.0, abs=0.01)


def test_main_window_survives_rapid_theme_toggles(qapp, main_window):
    for mode in (ThemeMode.DARK, ThemeMode.LIGHT, ThemeMode.DARK, ThemeMode.LIGHT):
        apply_theme(qapp, mode)
        main_window.style().unpolish(main_window)
        main_window.style().polish(main_window)
        main_window.rule_editor.name_edit.setText(f"Theme {mode.value}")
        main_window.rule_editor.commit_to_rule()
        assert main_window.document.rules[0].name == f"Theme {mode.value}"
    assert current_theme_mode(qapp) is ThemeMode.LIGHT
