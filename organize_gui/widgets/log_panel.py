"""Log panel for displaying organize run output and saving logs to disk."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional

from PyQt6.QtGui import QColor, QTextCharFormat, QTextCursor
from PyQt6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class LogPanel(QWidget):
    """Scrollable log view with clear and save actions.

    Messages are color-coded by level (info / warn / error).
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize the log panel UI."""
        super().__init__(parent)

        self._title = QLabel("Logs & errors", self)
        self._title.setStyleSheet("font-weight: bold;")

        self._view = QPlainTextEdit(self)
        self._view.setReadOnly(True)
        self._view.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
        self._view.setMaximumBlockCount(20000)
        self._view.setStyleSheet(
            "QPlainTextEdit { font-family: monospace; font-size: 12px; }"
        )

        self._clear_btn = QPushButton("Clear", self)
        self._clear_btn.clicked.connect(self.clear)
        self._save_btn = QPushButton("Save logs…", self)
        self._save_btn.clicked.connect(self.save_logs)

        btn_row = QHBoxLayout()
        btn_row.addWidget(self._title)
        btn_row.addStretch(1)
        btn_row.addWidget(self._clear_btn)
        btn_row.addWidget(self._save_btn)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(btn_row)
        layout.addWidget(self._view)

        self._plain_buffer: list[str] = []

    def append(self, message: str, level: str = "info") -> None:
        """Append a log line with level-based coloring.

        Args:
            message: Text to show (may be multi-line).
            level: One of ``info``, ``warn``, ``error``, ``success``, ``system``.
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        line = f"[{timestamp}] {message}"
        self._plain_buffer.append(line)

        fmt = QTextCharFormat()
        color = {
            "info": QColor("#222222"),
            "warn": QColor("#9a6b00"),
            "error": QColor("#b00020"),
            "success": QColor("#0b6b0b"),
            "system": QColor("#555555"),
        }.get(level, QColor("#222222"))
        fmt.setForeground(color)
        if level == "error":
            fmt.setFontWeight(700)

        cursor = self._view.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(line + "\n", fmt)
        self._view.setTextCursor(cursor)
        self._view.ensureCursorVisible()

    def clear(self) -> None:
        """Clear the log view and internal buffer."""
        self._view.clear()
        self._plain_buffer.clear()

    def save_logs(self) -> None:
        """Prompt for a file path and write the log buffer to disk."""
        if not self._plain_buffer:
            QMessageBox.information(self, "Save logs", "There are no logs to save.")
            return

        default_name = f"organize-log-{datetime.now().strftime('%Y%m%d-%H%M%S')}.txt"
        path_str, _ = QFileDialog.getSaveFileName(
            self,
            "Save logs",
            str(Path.home() / default_name),
            "Text files (*.txt);;All files (*)",
        )
        if not path_str:
            return
        try:
            Path(path_str).write_text("\n".join(self._plain_buffer) + "\n", encoding="utf-8")
            self.append(f"Logs saved to {path_str}", level="system")
        except OSError as exc:
            QMessageBox.critical(self, "Save logs failed", str(exc))

    def text(self) -> str:
        """Return the full plain-text log contents."""
        return "\n".join(self._plain_buffer)
