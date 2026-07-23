"""Application-wide visual theme (light/dark) for the organize GUI."""

from __future__ import annotations

from typing import Optional

from PyQt6.QtGui import QColor, QFont, QPalette
from PyQt6.QtWidgets import QApplication

from ui.styles.dpi import effective_ui_scale, scale_stylesheet, screen_scale_factor
from ui.styles.palette import ColorPalette, ThemeMode, palette_for
from ui.styles.system_theme import detect_system_theme


# Design tokens use 1x (96 DPI) pixels. Colors come from {palette tokens}.
# Important: never set a global QWidget transparent background — on Wayland /
# WSLg that makes the whole window see-through to apps behind it.
_STYLE_TEMPLATE = """
/* ---------- base ---------- */
* {{
    font-family: "Segoe UI", "SF Pro Text", "Ubuntu", "Cantarell", sans-serif;
}}

QMainWindow, QDialog {{
    background-color: {window_bg};
    color: {text};
}}

/* Central widget + generic containers must be opaque. */
QMainWindow > QWidget, QDialog > QWidget, QWidget#CentralRoot {{
    background-color: {window_bg};
    color: {text};
}}

QWidget {{
    color: {text};
}}

QSplitter {{
    background-color: {window_bg};
}}

QSplitter::handle {{
    background-color: {window_bg};
}}

/* Text-only labels stay clear of fills so they don't look like chips. */
QLabel {{
    background-color: transparent;
    color: {text};
}}

QMenuBar {{
    background-color: {panel_bg};
    border-bottom: 1px solid {border};
    padding: 2px 6px;
    color: {text};
}}

QMenuBar::item {{
    padding: 6px 10px;
    border-radius: 6px;
    background-color: transparent;
    color: {text};
}}

QMenuBar::item:selected {{
    background-color: {hover_bg};
}}

QMenu {{
    background-color: {panel_bg};
    border: 1px solid {border};
    border-radius: 8px;
    padding: 6px;
    color: {text};
}}

QMenu::item {{
    padding: 7px 18px;
    border-radius: 6px;
    color: {text};
}}

QMenu::item:selected {{
    background-color: {selected_bg};
    color: {accent};
}}

QStatusBar {{
    background-color: {panel_bg};
    border-top: 1px solid {border};
    color: {text_muted};
}}

QToolBar#MainToolbar {{
    background-color: {panel_bg};
    border: none;
    border-bottom: 1px solid {border};
    spacing: 8px;
    padding: 8px 12px;
}}

QToolBar#MainToolbar QToolButton {{
    background-color: {muted_bg};
    border: 1px solid {border};
    border-radius: 8px;
    padding: 7px 12px;
    margin-right: 2px;
    color: {text};
}}

QToolBar#MainToolbar QToolButton:hover {{
    background-color: {hover_bg};
    border-color: {border_strong};
}}

QToolBar#MainToolbar QToolButton:pressed {{
    background-color: {hover_bg};
}}

QToolBar#MainToolbar QToolButton#PrimaryButton {{
    background-color: {accent};
    color: {text_on_accent};
    border: 1px solid {accent};
    font-weight: 600;
}}

QToolBar#MainToolbar QToolButton#PrimaryButton:hover {{
    background-color: {accent_hover};
    border-color: {accent_hover};
}}

QToolBar#MainToolbar QToolButton#DangerButton {{
    background-color: {danger_bg};
    color: {danger_text};
    border: 1px solid {danger_border};
    font-weight: 600;
}}

QToolBar#MainToolbar QToolButton#DangerButton:hover {{
    background-color: {danger_bg};
    border-color: {danger_text};
}}

QFrame#SidePanel, QFrame#EditorPanel, QFrame#LogPanel {{
    background-color: {panel_bg};
    border: 1px solid {border};
    border-radius: 12px;
}}

QFrame#OptionsCard {{
    background-color: {card_bg};
    border: 1px solid {border};
    border-radius: 10px;
}}

QLabel#PanelTitle {{
    font-weight: 700;
    letter-spacing: 0.04em;
    color: {text_faint};
    padding: 2px 2px 8px 2px;
    background-color: transparent;
}}

QLabel#SectionTitle {{
    font-weight: 600;
    color: {text};
    padding: 2px 0 6px 0;
    background-color: transparent;
}}

QLabel#HintLabel {{
    color: {text_faint};
    background-color: transparent;
}}

QLabel#EmptyState {{
    color: {text_faint};
    padding: 48px 24px;
    background-color: transparent;
}}

QLineEdit, QComboBox, QSpinBox, QTextEdit, QPlainTextEdit {{
    background-color: {input_bg};
    border: 1px solid {border_strong};
    border-radius: 8px;
    padding: 7px 10px;
    color: {text};
    selection-background-color: {selection_bg};
    selection-color: {text};
}}

QLineEdit#RuleNameEdit {{
    font-size: 16px;
    font-weight: 600;
    padding: 10px 12px;
}}

QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QTextEdit:focus {{
    border: 1px solid {focus_border};
}}

QComboBox::drop-down {{
    border: none;
    width: 24px;
}}

QComboBox QAbstractItemView {{
    background-color: {panel_bg};
    color: {text};
    border: 1px solid {border};
    selection-background-color: {selected_bg};
}}

QListWidget {{
    background-color: {card_bg};
    border: 1px solid {border};
    border-radius: 10px;
    padding: 4px;
    outline: none;
    color: {text};
}}

QListWidget::item {{
    border-radius: 8px;
    padding: 10px 12px;
    margin: 2px 2px;
    color: {text};
}}

QListWidget::item:selected {{
    background-color: {selected_bg};
    color: {accent};
}}

QListWidget::item:hover:!selected {{
    background-color: {hover_bg};
}}

QListWidget#RuleList::item {{
    font-weight: 500;
}}

QPushButton {{
    background-color: {muted_bg};
    border: 1px solid {border};
    border-radius: 8px;
    padding: 7px 12px;
    min-height: 18px;
    color: {text};
}}

QPushButton:hover {{
    background-color: {hover_bg};
    border-color: {border_strong};
}}

QPushButton:pressed {{
    background-color: {hover_bg};
}}

QPushButton:disabled {{
    color: {text_faint};
    background-color: {card_bg};
}}

QPushButton#GhostButton {{
    background-color: {panel_bg};
    border: 1px solid {border};
    color: {text_muted};
    padding: 6px 8px;
}}

QPushButton#GhostButton:hover {{
    background-color: {hover_bg};
    border-color: {border_strong};
}}

QPushButton#AccentButton, QToolButton#AccentButton {{
    background-color: {accent};
    color: {text_on_accent};
    border: 1px solid {accent};
    font-weight: 600;
    border-radius: 8px;
    padding: 6px 10px;
}}

QPushButton#AccentButton:hover, QToolButton#AccentButton:hover {{
    background-color: {accent_hover};
    border-color: {accent_hover};
}}

QCheckBox {{
    spacing: 8px;
    padding: 2px 0;
    color: {text};
    background-color: transparent;
}}

QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border-radius: 4px;
    border: 1px solid {border_strong};
    background-color: {input_bg};
}}

QCheckBox::indicator:checked {{
    background-color: {accent};
    border-color: {accent};
}}

QTabWidget {{
    background-color: {panel_bg};
}}

QTabWidget::pane {{
    border: none;
    background-color: {panel_bg};
    top: -1px;
}}

QTabBar {{
    background-color: {panel_bg};
}}

QTabBar::tab {{
    background-color: {panel_bg};
    border: none;
    color: {text_faint};
    padding: 10px 16px;
    margin-right: 4px;
    border-bottom: 2px solid transparent;
    font-weight: 600;
}}

QTabBar::tab:selected {{
    color: {accent};
    border-bottom: 2px solid {accent};
    background-color: {panel_bg};
}}

QTabBar::tab:hover:!selected {{
    color: {text};
}}

/* Scroll areas must be opaque; transparent viewports show the desktop. */
QScrollArea {{
    border: none;
    background-color: {panel_bg};
}}

QScrollArea > QWidget > QWidget {{
    background-color: {panel_bg};
}}

QScrollBar:vertical {{
    background-color: {panel_bg};
    width: 10px;
    margin: 4px 2px 4px 0;
}}

QScrollBar::handle:vertical {{
    background-color: {border_strong};
    border-radius: 5px;
    min-height: 28px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {text_faint};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}

QSplitter::handle:horizontal {{
    width: 8px;
    background-color: {window_bg};
}}

QSplitter::handle:vertical {{
    height: 8px;
    background-color: {window_bg};
}}

QGroupBox {{
    background-color: {card_bg};
    border: 1px solid {border};
    border-radius: 10px;
    margin-top: 14px;
    padding: 16px 12px 12px 12px;
    font-weight: 600;
    color: {text};
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
    color: {text_muted};
}}

QToolTip {{
    background-color: {tooltip_bg};
    color: {tooltip_text};
    border: none;
    padding: 6px 8px;
    border-radius: 6px;
}}

QTextEdit#LogView {{
    font-family: "JetBrains Mono", "Cascadia Code", "Consolas", "Menlo", monospace;
    font-size: 12px;
    background-color: {log_bg};
    color: {log_text};
    border-radius: 10px;
    border: 1px solid {log_border};
    padding: 8px;
}}

QTextEdit#YamlView {{
    font-family: "JetBrains Mono", "Cascadia Code", "Consolas", "Menlo", monospace;
    font-size: 12px;
    background-color: {code_bg};
    color: {code_text};
    border: 1px solid {code_border};
    border-radius: 10px;
    padding: 12px;
}}

QLabel#HelpText {{
    color: {text_faint};
    font-size: 11px;
    background-color: transparent;
}}
"""


def build_stylesheet(palette: ColorPalette, sheet_scale: float) -> str:
    """Render and DPI-scale the stylesheet for *palette*."""
    rendered = _STYLE_TEMPLATE.format(**palette.as_map())
    return scale_stylesheet(rendered, sheet_scale)


def apply_qt_palette(app: QApplication, palette: ColorPalette) -> None:
    """Set a Fusion QPalette that matches the active color tokens."""
    qp = QPalette()
    window = QColor(palette.window_bg)
    QColor(palette.panel_bg)
    text = QColor(palette.text)
    muted = QColor(palette.text_muted)
    accent = QColor(palette.accent)
    base = QColor(palette.input_bg)
    highlight = QColor(palette.selected_bg)
    button = QColor(palette.muted_bg)

    qp.setColor(QPalette.ColorRole.Window, window)
    qp.setColor(QPalette.ColorRole.WindowText, text)
    qp.setColor(QPalette.ColorRole.Base, base)
    qp.setColor(QPalette.ColorRole.AlternateBase, QColor(palette.card_bg))
    qp.setColor(QPalette.ColorRole.Text, text)
    qp.setColor(QPalette.ColorRole.Button, button)
    qp.setColor(QPalette.ColorRole.ButtonText, text)
    qp.setColor(QPalette.ColorRole.BrightText, QColor(palette.text_on_accent))
    qp.setColor(QPalette.ColorRole.Highlight, highlight)
    qp.setColor(QPalette.ColorRole.HighlightedText, accent)
    qp.setColor(QPalette.ColorRole.ToolTipBase, QColor(palette.tooltip_bg))
    qp.setColor(QPalette.ColorRole.ToolTipText, QColor(palette.tooltip_text))
    qp.setColor(QPalette.ColorRole.PlaceholderText, muted)
    qp.setColor(QPalette.ColorRole.Link, accent)
    app.setPalette(qp)


def apply_theme(
    app: QApplication,
    mode: Optional[ThemeMode] = None,
) -> float:
    """Apply Fusion style, palette, and stylesheet for *mode* (or system).

    Returns the effective UI scale factor.
    """
    app.setStyle("Fusion")

    resolved = mode or detect_system_theme()
    palette = palette_for(resolved)

    sheet_scale = screen_scale_factor(app)
    app.setStyleSheet(build_stylesheet(palette, sheet_scale))
    apply_qt_palette(app, palette)

    font = QFont("Segoe UI")
    if not font.exactMatch():
        font = QFont()
    font.setPointSizeF(10.5)
    app.setFont(font)

    scale = effective_ui_scale(app)
    app.setProperty("ui_scale", scale)
    app.setProperty("stylesheet_scale", sheet_scale)
    app.setProperty("theme_mode", resolved.value)
    app.setProperty("color_palette", palette)
    return scale


def current_theme_mode(app: QApplication | None = None) -> ThemeMode:
    """Return the currently applied theme mode."""
    application = app or QApplication.instance()
    if application is not None:
        value = application.property("theme_mode")
        if value in {ThemeMode.LIGHT.value, ThemeMode.DARK.value}:
            return ThemeMode(str(value))
    return detect_system_theme()


def current_palette(app: QApplication | None = None) -> ColorPalette:
    """Return the active :class:`ColorPalette` (falls back to system)."""
    application = app or QApplication.instance()
    if application is not None:
        stored = application.property("color_palette")
        if isinstance(stored, ColorPalette):
            return stored
    return palette_for(current_theme_mode(application))  # type: ignore[arg-type]


def ui_scale(app: QApplication | None = None) -> float:
    """Return the scale for stylesheet ``px`` / ``sp()`` helpers."""
    application = app or QApplication.instance()
    if application is not None:
        stored = application.property("stylesheet_scale")
        if stored is not None and stored != "":
            try:
                return float(stored)
            except (TypeError, ValueError):
                pass
    return screen_scale_factor(application)  # type: ignore[arg-type]
