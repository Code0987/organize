"""Path picker widget combining a line edit with a browse button."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QWidget,
)


class PathPicker(QWidget):
    """A line edit plus browse button for selecting a filesystem path.

    Signals:
        path_changed: Emitted with the current text whenever it changes.
    """

    path_changed = pyqtSignal(str)

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        *,
        directory_mode: bool = True,
        placeholder: str = "",
    ) -> None:
        """Initialize the path picker.

        Args:
            parent: Optional parent widget.
            directory_mode: If True, browse for directories; otherwise files.
            placeholder: Placeholder text for the line edit.
        """
        super().__init__(parent)
        self._directory_mode = directory_mode

        self._edit = QLineEdit(self)
        self._edit.setPlaceholderText(placeholder)
        self._edit.textChanged.connect(self.path_changed.emit)

        self._browse = QPushButton("Browse…", self)
        self._browse.setFixedWidth(90)
        self._browse.clicked.connect(self._on_browse)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._edit, stretch=1)
        layout.addWidget(self._browse)

    def text(self) -> str:
        """Return the current path text."""
        return self._edit.text()

    def set_text(self, value: str) -> None:
        """Set the path text without disrupting the cursor unnecessarily."""
        if self._edit.text() != value:
            self._edit.setText(value)

    def set_directory_mode(self, directory_mode: bool) -> None:
        """Switch between directory and file browse dialogs."""
        self._directory_mode = directory_mode

    def _on_browse(self) -> None:
        """Open a file or directory dialog and update the line edit."""
        start = self._edit.text().strip() or str(Path.home())
        if self._directory_mode:
            chosen = QFileDialog.getExistingDirectory(
                self,
                "Select directory",
                start,
            )
        else:
            chosen, _ = QFileDialog.getOpenFileName(
                self,
                "Select file",
                start,
            )
        if chosen:
            self._edit.setText(chosen)
