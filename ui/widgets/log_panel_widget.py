"""Panel that displays organize run logs and allows saving them."""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QTextCharFormat, QTextCursor
from PyQt6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ui.services.capture_output import LogEntry


class LogPanelWidget(QWidget):
    """Scrollable colored log view with clear / save actions."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._entries: List[LogEntry] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        header = QHBoxLayout()
        title = QLabel("Activity")
        title.setObjectName("PanelTitle")
        header.addWidget(title)
        header.addStretch(1)

        self.clear_btn = QPushButton("Clear")
        self.clear_btn.setObjectName("GhostButton")
        self.clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.save_btn = QPushButton("Save logs…")
        self.save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        header.addWidget(self.clear_btn)
        header.addWidget(self.save_btn)
        layout.addLayout(header)

        self.view = QTextEdit()
        self.view.setObjectName("LogView")
        self.view.setReadOnly(True)
        self.view.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self.view.setPlaceholderText("Dry-run or run a config to see results here…")
        layout.addWidget(self.view)

        self.clear_btn.clicked.connect(self.clear)
        self.save_btn.clicked.connect(self.save_to_file)

    def append_entry(self, entry: LogEntry) -> None:
        """Append one log entry to the view."""
        self._entries.append(entry)
        fmt = QTextCharFormat()
        level = entry.level.lower()
        if level == "error":
            fmt.setForeground(QColor("#ff6b6b"))
        elif level == "warn":
            fmt.setForeground(QColor("#ffd43b"))
        else:
            fmt.setForeground(QColor("#91d5ff"))

        cursor = self.view.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(entry.format_line() + "\n", fmt)
        self.view.setTextCursor(cursor)
        self.view.ensureCursorVisible()

    def append_message(self, level: str, message: str) -> None:
        """Append a free-form message without a full :class:`LogEntry`."""
        from datetime import datetime, timezone

        self.append_entry(
            LogEntry(
                timestamp=datetime.now(timezone.utc),
                level=level,
                message=message,
            )
        )

    def clear(self) -> None:
        """Remove all log content."""
        self._entries.clear()
        self.view.clear()

    def save_to_file(self) -> None:
        """Prompt for a path and write all log lines as plain text."""
        path_str, _ = QFileDialog.getSaveFileName(
            self,
            "Save logs",
            "organize-gui.log",
            "Log files (*.log *.txt);;All files (*)",
        )
        if not path_str:
            return
        path = Path(path_str)
        try:
            text = "\n".join(entry.format_line() for entry in self._entries)
            if text and not text.endswith("\n"):
                text += "\n"
            path.write_text(text, encoding="utf-8")
        except OSError as exc:
            QMessageBox.critical(self, "Save failed", str(exc))
            return
        QMessageBox.information(self, "Saved", f"Logs written to:\n{path}")

    def plain_text(self) -> str:
        """Return the full log as plain text."""
        return "\n".join(entry.format_line() for entry in self._entries)
