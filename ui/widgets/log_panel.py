"""Run log: messages, errors, and export to a file."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QTextCursor
from PyQt6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class LogPanel(QWidget):
    """Shows organize output as a table and a timestamped text log.

    Users can save the full log or only the error lines.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._lines: List[str] = []
        self._errors: List[str] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        self.banner = QLabel("No run yet. Use Dry run to preview matches.")
        self.banner.setStyleSheet("color: #94a3b8; padding: 4px 2px;")
        layout.addWidget(self.banner)

        splitter = QSplitter(Qt.Orientation.Vertical)
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(
            ["Level", "Rule", "Path", "Source", "Message"]
        )
        self.table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.Stretch
        )
        self.table.horizontalHeader().setSectionResizeMode(
            4, QHeaderView.ResizeMode.Stretch
        )
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        splitter.addWidget(self.table)

        self.text = QTextEdit()
        self.text.setReadOnly(True)
        self.text.setPlaceholderText("Timestamped log output appears here.")
        splitter.addWidget(self.text)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 1)
        layout.addWidget(splitter, 1)

        stats = QHBoxLayout()
        self.success_label = QLabel("success 0")
        self.success_label.setStyleSheet("color: #34d399;")
        self.error_label = QLabel("fail 0")
        self.error_label.setStyleSheet("color: #f87171;")
        stats.addWidget(self.success_label)
        stats.addWidget(self.error_label)
        stats.addStretch(1)
        save_all = QPushButton("Save log…")
        save_err = QPushButton("Save errors…")
        clear = QPushButton("Clear")
        save_all.clicked.connect(self.save_log)
        save_err.clicked.connect(self.save_errors)
        clear.clicked.connect(self.clear)
        stats.addWidget(save_all)
        stats.addWidget(save_err)
        stats.addWidget(clear)
        layout.addLayout(stats)

    def reset(self, simulate: bool, working_dir: str) -> None:
        """Start a new run log."""
        self.table.setRowCount(0)
        self.text.clear()
        self._lines.clear()
        self._errors.clear()
        mode = "Dry run" if simulate else "Run"
        heading = f"{mode} in {working_dir}"
        self.banner.setText(heading)
        self.banner.setStyleSheet(
            "color: #34d399; padding: 4px 2px;"
            if simulate
            else "color: #fbbf24; padding: 4px 2px;"
        )
        self.success_label.setText("success 0")
        self.error_label.setText("fail 0")
        self._append_text("INFO", heading)

    def add_message(self, event: Dict) -> None:
        """Append one organize message to the table and the text log."""
        row = self.table.rowCount()
        self.table.insertRow(row)
        values = [
            str(event.get("level", "info")),
            event.get("rule_name") or f"#{event.get('rule_nr', 0)}",
            str(event.get("path", "")),
            str(event.get("sender", "")),
            str(event.get("msg", "")),
        ]
        color = {
            "info": QColor("#e5e7eb"),
            "warn": QColor("#fbbf24"),
            "error": QColor("#f87171"),
        }.get(str(event.get("level", "info")), QColor("#e5e7eb"))
        for column, value in enumerate(values):
            item = QTableWidgetItem(value)
            item.setForeground(color)
            if column == 0:
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, column, item)
        self.table.scrollToBottom()
        level = str(event.get("level", "info")).upper()
        path = event.get("path") or ""
        message = event.get("msg") or ""
        line = f"{level}  {path}  {message}".strip()
        self._append_text(level, line)
        if level == "ERROR":
            self._errors.append(self._lines[-1])

    def finish(self, success: int, errors: int) -> None:
        """Record the organize summary counts."""
        self.success_label.setText(f"success {success}")
        self.error_label.setText(f"fail {errors}")
        if success == 0 and errors == 0:
            suffix = (
                "  —  nothing to do (no files matched). "
                "If that is unexpected, check the warnings above: "
                "the folder may not exist, may be empty, or a filter "
                "(extension, name, …) excluded every file."
            )
        else:
            suffix = f"  —  {success} ok / {errors} failed"
        self.banner.setText(self.banner.text() + suffix)
        self._append_text("INFO", f"Finished{suffix}")

    def fail(self, message: str) -> None:
        """Show a run-level failure (config parse error, etc.)."""
        self.banner.setText(f"Failed: {message}")
        self.banner.setStyleSheet("color: #f87171; padding: 4px 2px;")
        self._append_text("ERROR", message)
        self._errors.append(self._lines[-1])

    def save_log(self) -> None:
        """Write the full timestamped log to a file the user chooses."""
        self._save(self._lines, "Save log", "organize-run.log")

    def save_errors(self) -> None:
        """Write only error lines to a file the user chooses."""
        if not self._errors:
            QMessageBox.information(self, "No errors", "There are no errors to save.")
            return
        self._save(self._errors, "Save errors", "organize-errors.log")

    def clear(self) -> None:
        """Empty the table, text log, and counters."""
        self.reset(simulate=True, working_dir="(cleared)")
        self.banner.setText("Log cleared.")
        self.banner.setStyleSheet("color: #94a3b8; padding: 4px 2px;")

    def _append_text(self, level: str, message: str) -> None:
        stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{stamp}] [{level}] {message}"
        self._lines.append(line)
        self.text.append(line)
        self.text.moveCursor(QTextCursor.MoveOperation.End)

    def _save(self, lines: List[str], title: str, suggested: str) -> None:
        path, _filter = QFileDialog.getSaveFileName(
            self,
            title,
            str(Path.home() / suggested),
            "Log files (*.log *.txt);;All files (*)",
        )
        if not path:
            return
        try:
            Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")
        except OSError as exc:
            QMessageBox.critical(self, "Could not save log", str(exc))
            return
        QMessageBox.information(self, "Saved", f"Wrote {len(lines)} line(s) to\n{path}")
