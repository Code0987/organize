"""Application window icon painted at runtime (no asset file required)."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QIcon, QPainter, QPixmap


class AppIcon:
    """Tiny folder glyph used as the window / taskbar icon."""

    def build(self) -> QIcon:
        """Return a 64×64 icon."""
        pix = QPixmap(64, 64)
        pix.fill(QColor("#0b1220"))
        painter = QPainter(pix)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QColor("#38bdf8"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(10, 16, 44, 34, 8, 8)
        painter.setBrush(QColor("#0b1220"))
        painter.drawRect(18, 28, 12, 14)
        painter.drawRect(34, 24, 12, 18)
        painter.end()
        return QIcon(pix)
