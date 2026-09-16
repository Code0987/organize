"""Fusion stylesheet and palette for the organize desktop UI."""

from __future__ import annotations

from PyQt6.QtGui import QColor, QFont, QPalette
from PyQt6.QtWidgets import QApplication

from ui.constants import (
    ACCENT,
    ACCENT_HOVER,
    BG,
    BORDER,
    DANGER,
    ELEVATED,
    MUTED,
    SUCCESS,
    SURFACE,
    TEXT,
)


class Theme:
    """Apply the dark Fusion look used by every window."""

    def apply(self, app: QApplication) -> None:
        """Set Fusion style, palette, and the global stylesheet."""
        app.setStyle("Fusion")
        # 11 pt matches typical Windows Segoe UI; HiDPI scale is applied on top.
        font = QFont("Segoe UI")
        if not font.exactMatch():
            font = QFont("Ubuntu")
        font.setPointSize(11)
        font.setHintingPreference(QFont.HintingPreference.PreferFullHinting)
        font.setStyleStrategy(
            QFont.StyleStrategy.PreferAntialias | QFont.StyleStrategy.PreferQuality
        )
        app.setFont(font)
        app.setPalette(self._palette())
        app.setStyleSheet(self._stylesheet())

    def _palette(self) -> QPalette:
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(BG))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(TEXT))
        palette.setColor(QPalette.ColorRole.Base, QColor(SURFACE))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(ELEVATED))
        palette.setColor(QPalette.ColorRole.Text, QColor(TEXT))
        palette.setColor(QPalette.ColorRole.Button, QColor(ELEVATED))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(TEXT))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(ACCENT))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#0b1220"))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(ELEVATED))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(TEXT))
        palette.setColor(QPalette.ColorRole.PlaceholderText, QColor(MUTED))
        return palette

    def _stylesheet(self) -> str:
        return f"""
QMainWindow, QDialog, QWidget {{
    background: {BG};
    color: {TEXT};
}}
QToolBar {{
    background: {SURFACE};
    border: none;
    border-bottom: 1px solid {BORDER};
    spacing: 8px;
    padding: 8px 12px;
}}
QStatusBar {{
    background: {SURFACE};
    color: {MUTED};
    border-top: 1px solid {BORDER};
}}
QSplitter::handle {{
    background: {BORDER};
    width: 1px;
}}
QListWidget, QTreeWidget, QTableWidget, QPlainTextEdit, QTextEdit, QLineEdit,
QComboBox, QSpinBox {{
    background: {SURFACE};
    color: {TEXT};
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 6px 8px;
    selection-background-color: {ACCENT};
    selection-color: #0b1220;
}}
QListWidget::item {{
    padding: 8px 10px;
    border-radius: 6px;
}}
QListWidget::item:selected {{
    background: {ELEVATED};
    color: {TEXT};
    border: 1px solid {ACCENT};
}}
QTableWidget {{
    gridline-color: {BORDER};
}}
QHeaderView::section {{
    background: {ELEVATED};
    color: {MUTED};
    border: none;
    border-bottom: 1px solid {BORDER};
    padding: 6px 8px;
}}
QPushButton {{
    background: {ELEVATED};
    color: {TEXT};
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 7px 14px;
}}
QPushButton:hover {{
    border-color: {ACCENT};
    color: {ACCENT_HOVER};
}}
QPushButton:disabled {{
    color: {MUTED};
    border-color: {BORDER};
}}
QPushButton#accent {{
    background: {ACCENT};
    color: #0b1220;
    border: none;
    font-weight: 600;
}}
QPushButton#accent:hover {{
    background: {ACCENT_HOVER};
}}
QPushButton#danger {{
    background: #7f1d1d;
    color: #fecaca;
    border: 1px solid #991b1b;
}}
QPushButton#success {{
    background: #064e3b;
    color: {SUCCESS};
    border: 1px solid #047857;
}}
QTabWidget::pane {{
    border: 1px solid {BORDER};
    border-radius: 10px;
    top: -1px;
    background: {BG};
}}
QTabBar::tab {{
    background: transparent;
    color: {MUTED};
    padding: 8px 16px;
    border-bottom: 2px solid transparent;
}}
QTabBar::tab:selected {{
    color: {TEXT};
    border-bottom: 2px solid {ACCENT};
}}
QGroupBox {{
    border: 1px solid {BORDER};
    border-radius: 10px;
    margin-top: 14px;
    padding: 12px 10px 10px 10px;
    font-weight: 600;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
    color: {MUTED};
}}
QCheckBox, QRadioButton, QLabel {{
    color: {TEXT};
}}
QMenuBar {{
    background: {SURFACE};
    color: {TEXT};
}}
QMenu {{
    background: {SURFACE};
    color: {TEXT};
    border: 1px solid {BORDER};
}}
QMenu::item:selected {{
    background: {ELEVATED};
}}
"""
