"""One row in the New Config preset list."""

from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QLabel, QSizePolicy, QVBoxLayout, QWidget

from ui.models.preset import Preset


class PresetRow(QWidget):
    """Title + description for a single starter config.

    QListWidgetItem cannot size multiline text reliably (especially with
    stylesheet padding and HiDPI), so each preset is a real widget.
    """

    def __init__(self, preset: Preset, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(3)

        title = QLabel(preset.title)
        title_font = QFont(self.font())
        title_font.setPointSize(max(self.font().pointSize(), 11))
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet("color: #e5e7eb; background: transparent;")
        title.setWordWrap(True)

        description = QLabel(preset.description)
        description.setWordWrap(True)
        description.setStyleSheet("color: #94a3b8; background: transparent;")

        layout.addWidget(title)
        layout.addWidget(description)

        # Force a height that includes both labels + margins so rows cannot stack.
        self.adjustSize()
        hint = self.sizeHint()
        self.setMinimumHeight(max(hint.height(), 56))
        self.setToolTip(f"{preset.title}\n{preset.description}")
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
