"""Left-hand list of discovered organize config files."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class Sidebar(QWidget):
    """Brand header plus a list of configs from the default locations."""

    open_requested = pyqtSignal(Path)
    new_requested = pyqtSignal()
    browse_requested = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 16, 14, 14)
        layout.setSpacing(10)

        # Fonts are set on the widgets (not only in CSS) so Qt's sizeHint
        # matches the painted text and the wordmark cannot overlap "Desktop".
        header = QWidget()
        header.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 8)
        header_layout.setSpacing(2)

        brand = QLabel("organize")
        brand_font = QFont(self.font())
        brand_font.setPointSize(18)
        brand_font.setBold(True)
        brand.setFont(brand_font)
        brand.setStyleSheet("color: #38bdf8; background: transparent;")
        brand.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        subtitle = QLabel("Desktop")
        sub_font = QFont(self.font())
        sub_font.setPointSize(10)
        subtitle.setFont(sub_font)
        subtitle.setStyleSheet("color: #94a3b8; background: transparent;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        header_layout.addWidget(brand)
        header_layout.addWidget(subtitle)
        layout.addWidget(header)

        heading = QLabel("CONFIGS")
        heading_font = QFont(self.font())
        heading_font.setPointSize(9)
        heading_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1.2)
        heading.setFont(heading_font)
        heading.setStyleSheet("color: #64748b; background: transparent;")
        layout.addWidget(heading)

        self.list = QListWidget()
        self.list.itemActivated.connect(self._activate)
        self.list.itemClicked.connect(self._activate)
        self.empty = QLabel("No configs in the default folders yet.\nUse New or Open…")
        self.empty.setWordWrap(True)
        self.empty.setStyleSheet("color: #64748b; padding: 8px;")
        layout.addWidget(self.list, 1)
        layout.addWidget(self.empty, 1)

        buttons = QHBoxLayout()
        new_btn = QPushButton("New")
        open_btn = QPushButton("Open…")
        new_btn.clicked.connect(self.new_requested.emit)
        open_btn.clicked.connect(self.browse_requested.emit)
        buttons.addWidget(new_btn)
        buttons.addWidget(open_btn)
        layout.addLayout(buttons)

    def set_configs(
        self,
        paths: Iterable[Path],
        current: Optional[Path] = None,
    ) -> None:
        """Replace the list contents and highlight ``current`` if present."""
        self.list.clear()
        current_resolved = current.resolve() if current else None
        count = 0
        for path in paths:
            item = QListWidgetItem(path.stem)
            item.setToolTip(str(path))
            item.setData(Qt.ItemDataRole.UserRole, str(path))
            self.list.addItem(item)
            count += 1
            if current_resolved and path.resolve() == current_resolved:
                self.list.setCurrentItem(item)
        self.empty.setVisible(count == 0)
        self.list.setVisible(count > 0)

    def _activate(self, item: QListWidgetItem) -> None:
        path = item.data(Qt.ItemDataRole.UserRole)
        if path:
            self.open_requested.emit(Path(path))
