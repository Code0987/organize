"""Top toolbar: document title, working dir, tags, dry-run / run."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QFileDialog,
    QLabel,
    QLineEdit,
    QPushButton,
    QToolBar,
    QWidget,
)


class MainToolbar(QToolBar):
    """Primary actions for checking, dry-running, and applying rules."""

    check_requested = pyqtSignal()
    dry_run_requested = pyqtSignal()
    run_requested = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__("Main", parent)
        self.setMovable(False)

        self.title_label = QLabel("Untitled")
        self.title_label.setStyleSheet("font-weight: 700; font-size: 14px;")
        self.addWidget(self.title_label)
        self.addSeparator()

        self.addWidget(QLabel(" Working dir "))
        self.working_dir = QLineEdit(str(Path.home()))
        self.working_dir.setMinimumWidth(200)
        self.addWidget(self.working_dir)
        browse = QPushButton("…")
        browse.setFixedWidth(36)
        browse.clicked.connect(self._pick_working_dir)
        self.addWidget(browse)
        self.addSeparator()

        self.addWidget(QLabel(" Tags "))
        self.tags_edit = QLineEdit()
        self.tags_edit.setPlaceholderText("only these tags")
        self.tags_edit.setFixedWidth(140)
        self.addWidget(self.tags_edit)
        self.skip_tags_edit = QLineEdit()
        self.skip_tags_edit.setPlaceholderText("skip tags")
        self.skip_tags_edit.setFixedWidth(120)
        self.addWidget(self.skip_tags_edit)
        self.addSeparator()

        check_btn = QPushButton("Check")
        dry_btn = QPushButton("Dry run")
        dry_btn.setObjectName("accent")
        dry_btn.setToolTip("Simulate the current rules without changing any files.")
        run_btn = QPushButton("Run")
        run_btn.setObjectName("danger")
        run_btn.setToolTip("Apply the current rules to disk.")
        check_btn.clicked.connect(self.check_requested.emit)
        dry_btn.clicked.connect(self.dry_run_requested.emit)
        run_btn.clicked.connect(self.run_requested.emit)
        self.addWidget(check_btn)
        self.addWidget(dry_btn)
        self.addWidget(run_btn)

    def set_title(self, title: str) -> None:
        """Update the document name shown at the left of the bar."""
        self.title_label.setText(title)

    def working_directory(self) -> Path:
        """Working directory organize will ``chdir`` into."""
        return Path(self.working_dir.text() or ".").expanduser()

    def tags(self) -> str:
        """Raw comma-separated include-tags field."""
        return self.tags_edit.text()

    def skip_tags(self) -> str:
        """Raw comma-separated skip-tags field."""
        return self.skip_tags_edit.text()

    def _pick_working_dir(self) -> None:
        chosen = QFileDialog.getExistingDirectory(
            self, "Working directory", self.working_dir.text()
        )
        if chosen:
            self.working_dir.setText(chosen)
