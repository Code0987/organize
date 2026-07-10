"""Main application window for the organize rule editor GUI."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QCloseEvent, QKeySequence
from PyQt6.QtWidgets import (
    QFileDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from organize_gui.models.config_document import ConfigDocument
from organize_gui.services.config_service import ConfigService
from organize_gui.widgets.log_panel import LogPanel
from organize_gui.widgets.rule_editor import RuleEditorWidget
from organize_gui.widgets.rule_list import RuleListWidget
from organize_gui.workers.organize_worker import OrganizeWorker


class MainWindow(QMainWindow):
    """Top-level window: rule list, interactive editor, logs, and run controls."""

    def __init__(self) -> None:
        """Build the main window UI and connect signals."""
        super().__init__()
        self.setWindowTitle("organize — Rule Editor")
        self.resize(1200, 800)

        self._document = ConfigDocument.create_empty()
        self._worker: Optional[OrganizeWorker] = None

        self._rule_list = RuleListWidget(self)
        self._rule_editor = RuleEditorWidget(self)
        self._log_panel = LogPanel(self)

        self._status_label = QLabel("Ready", self)

        left = QWidget(self)
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(4, 4, 4, 4)
        left_layout.addWidget(QLabel("Rules", left))
        left_layout.addWidget(self._rule_list)

        center_split = QSplitter(Qt.Orientation.Horizontal, self)
        center_split.addWidget(left)
        center_split.addWidget(self._rule_editor)
        center_split.setStretchFactor(0, 0)
        center_split.setStretchFactor(1, 1)
        center_split.setSizes([220, 900])

        vertical = QSplitter(Qt.Orientation.Vertical, self)
        vertical.addWidget(center_split)
        vertical.addWidget(self._log_panel)
        vertical.setStretchFactor(0, 3)
        vertical.setStretchFactor(1, 1)
        vertical.setSizes([560, 220])

        container = QWidget(self)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.addWidget(vertical)
        self.setCentralWidget(container)

        self._build_actions()
        self._build_menus()
        self._build_toolbar()
        self.statusBar().addWidget(self._status_label, stretch=1)

        self._rule_list.selection_changed.connect(self._on_rule_selected)
        self._rule_list.rules_modified.connect(self._on_rules_modified)
        self._rule_editor.rule_changed.connect(self._on_rule_changed)

        self._load_document(self._document)
        self._log_panel.append(
            "Welcome to the organize rule editor. "
            "Create or open a config, edit rules interactively, then Dry-run or Run.",
            level="system",
        )

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_actions(self) -> None:
        """Create reusable QAction instances for menus and the toolbar."""
        self.act_new = QAction("New config", self)
        self.act_new.setShortcut(QKeySequence.StandardKey.New)
        self.act_new.triggered.connect(self.new_config)

        self.act_open = QAction("Open…", self)
        self.act_open.setShortcut(QKeySequence.StandardKey.Open)
        self.act_open.triggered.connect(self.open_config)

        self.act_save = QAction("Save", self)
        self.act_save.setShortcut(QKeySequence.StandardKey.Save)
        self.act_save.triggered.connect(self.save_config)

        self.act_save_as = QAction("Save as…", self)
        self.act_save_as.setShortcut(QKeySequence.StandardKey.SaveAs)
        self.act_save_as.triggered.connect(self.save_config_as)

        self.act_validate = QAction("Validate", self)
        self.act_validate.triggered.connect(self.validate_config)

        self.act_show_yaml = QAction("Show YAML preview", self)
        self.act_show_yaml.triggered.connect(self.show_yaml_preview)

        self.act_dry_run = QAction("Dry-run (simulate)", self)
        self.act_dry_run.setShortcut("Ctrl+D")
        self.act_dry_run.triggered.connect(lambda: self.run_config(simulate=True))

        self.act_run = QAction("Run", self)
        self.act_run.setShortcut("Ctrl+R")
        self.act_run.triggered.connect(lambda: self.run_config(simulate=False))

        self.act_stop = QAction("Stop", self)
        self.act_stop.setEnabled(False)
        self.act_stop.triggered.connect(self.stop_run)

        self.act_quit = QAction("Quit", self)
        self.act_quit.setShortcut(QKeySequence.StandardKey.Quit)
        self.act_quit.triggered.connect(self.close)

        self.act_about = QAction("About", self)
        self.act_about.triggered.connect(self.show_about)

    def _build_menus(self) -> None:
        """Populate the menu bar."""
        file_menu = self.menuBar().addMenu("&File")
        file_menu.addAction(self.act_new)
        file_menu.addAction(self.act_open)
        file_menu.addSeparator()
        file_menu.addAction(self.act_save)
        file_menu.addAction(self.act_save_as)
        file_menu.addSeparator()
        file_menu.addAction(self.act_quit)

        rule_menu = self.menuBar().addMenu("&Rules")
        rule_menu.addAction(self.act_validate)
        rule_menu.addAction(self.act_show_yaml)

        run_menu = self.menuBar().addMenu("R&un")
        run_menu.addAction(self.act_dry_run)
        run_menu.addAction(self.act_run)
        run_menu.addAction(self.act_stop)

        help_menu = self.menuBar().addMenu("&Help")
        help_menu.addAction(self.act_about)

    def _build_toolbar(self) -> None:
        """Create the main toolbar."""
        toolbar = QToolBar("Main", self)
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        toolbar.addAction(self.act_new)
        toolbar.addAction(self.act_open)
        toolbar.addAction(self.act_save)
        toolbar.addSeparator()
        toolbar.addAction(self.act_validate)
        toolbar.addSeparator()
        toolbar.addAction(self.act_dry_run)
        toolbar.addAction(self.act_run)
        toolbar.addAction(self.act_stop)

    # ------------------------------------------------------------------
    # Document management
    # ------------------------------------------------------------------

    def _load_document(self, document: ConfigDocument) -> None:
        """Replace the current document and refresh the UI."""
        self._document = document
        self._rule_list.set_rules(document.rules, select_index=0)
        if document.rules:
            self._rule_editor.set_rule(document.rules[0])
        else:
            self._rule_editor.set_rule(None)
        self._update_title()

    def _update_title(self) -> None:
        """Refresh the window title from the document state."""
        self.setWindowTitle(f"organize — {self._document.display_title()}")

    def _mark_dirty(self) -> None:
        """Mark the document dirty and update the title."""
        self._document.mark_dirty()
        self._update_title()

    def _confirm_discard(self) -> bool:
        """Ask the user to save/discard/cancel when there are unsaved changes."""
        if not self._document.dirty:
            return True
        result = QMessageBox.question(
            self,
            "Unsaved changes",
            "The current configuration has unsaved changes. Save before continuing?",
            QMessageBox.StandardButton.Save
            | QMessageBox.StandardButton.Discard
            | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Save,
        )
        if result == QMessageBox.StandardButton.Cancel:
            return False
        if result == QMessageBox.StandardButton.Save:
            return self.save_config()
        return True

    def new_config(self) -> None:
        """Create a new empty configuration."""
        if not self._confirm_discard():
            return
        self._load_document(ConfigDocument.create_empty())
        self._log_panel.append("Created a new configuration.", level="system")
        self._status_label.setText("New configuration")

    def open_config(self) -> None:
        """Open a config YAML file from disk."""
        if not self._confirm_discard():
            return
        start = ConfigService.default_config_dir()
        path_str, _ = QFileDialog.getOpenFileName(
            self,
            "Open organize config",
            str(start),
            "YAML files (*.yaml *.yml);;All files (*)",
        )
        if not path_str:
            return
        path = Path(path_str)
        try:
            document = ConfigService.load_path(path)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Open failed", str(exc))
            return
        self._load_document(document)
        self._log_panel.append(f"Opened {path}", level="system")
        self._status_label.setText(f"Opened {path.name}")

    def _commit_editor(self) -> None:
        """Flush in-progress rule editor fields into the document model."""
        self._rule_editor.commit_pending_edits()

    def save_config(self) -> bool:
        """Save the current config, prompting for a path if needed.

        Returns:
            True if the file was saved successfully.
        """
        self._commit_editor()
        if self._document.source_path is None:
            return self.save_config_as()
        try:
            ConfigService.save(self._document)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Save failed", str(exc))
            return False
        self._update_title()
        self._log_panel.append(f"Saved {self._document.source_path}", level="system")
        self._status_label.setText("Saved")
        return True

    def save_config_as(self) -> bool:
        """Save the config under a new path.

        Returns:
            True if the file was saved successfully.
        """
        self._commit_editor()
        start_dir = ConfigService.default_config_dir()
        start_dir.mkdir(parents=True, exist_ok=True)
        default = self._document.source_path or (start_dir / "config.yaml")
        path_str, _ = QFileDialog.getSaveFileName(
            self,
            "Save organize config",
            str(default),
            "YAML files (*.yaml *.yml);;All files (*)",
        )
        if not path_str:
            return False
        path = Path(path_str)
        if path.suffix.lower() not in (".yaml", ".yml"):
            path = path.with_suffix(".yaml")
        try:
            ConfigService.save(self._document, path)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Save failed", str(exc))
            return False
        self._update_title()
        self._log_panel.append(f"Saved {path}", level="system")
        self._status_label.setText(f"Saved as {path.name}")
        return True

    def validate_config(self) -> None:
        """Validate the current document with organize's parser."""
        self._commit_editor()
        ok, message = ConfigService.validate(self._document)
        if ok:
            self._log_panel.append(message, level="success")
            self._status_label.setText("Configuration is valid")
            QMessageBox.information(self, "Validate", message)
        else:
            self._log_panel.append(message, level="error")
            self._status_label.setText("Validation failed")
            QMessageBox.warning(self, "Validate", message)

    def show_yaml_preview(self) -> None:
        """Show the generated YAML in a message dialog and the log."""
        self._commit_editor()
        yaml_text = ConfigService.to_yaml(self._document)
        self._log_panel.append("── YAML preview ──", level="system")
        for line in yaml_text.splitlines():
            self._log_panel.append(line, level="info")
        # Also a dialog for quick viewing
        box = QMessageBox(self)
        box.setWindowTitle("YAML preview")
        box.setText("Current configuration as YAML:")
        box.setDetailedText(yaml_text)
        box.setIcon(QMessageBox.Icon.Information)
        box.exec()

    # ------------------------------------------------------------------
    # Run / dry-run
    # ------------------------------------------------------------------

    def run_config(self, simulate: bool = True) -> None:
        """Validate and execute the current configuration.

        Args:
            simulate: If True, perform a dry-run without modifying files.
        """
        self._commit_editor()
        if self._worker is not None and self._worker.isRunning():
            QMessageBox.warning(
                self,
                "Busy",
                "A run is already in progress. Stop it before starting another.",
            )
            return

        if not self._document.rules:
            QMessageBox.warning(self, "No rules", "Add at least one rule before running.")
            return

        ok, message = ConfigService.validate(self._document)
        if not ok:
            self._log_panel.append(message, level="error")
            QMessageBox.critical(
                self,
                "Invalid configuration",
                f"Cannot run: configuration is invalid.\n\n{message}",
            )
            return

        if not simulate:
            answer = QMessageBox.question(
                self,
                "Confirm live run",
                "This will modify files on disk according to your rules.\n\n"
                "Consider using Dry-run first. Continue with a live run?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
                return

        yaml_text = ConfigService.to_yaml(self._document)
        mode = "dry-run" if simulate else "live run"
        self._log_panel.append(f"Starting {mode}…", level="system")
        self._status_label.setText(f"Running ({mode})…")
        self._set_running(True)

        working_dir = str(Path.cwd())
        self._worker = OrganizeWorker(
            yaml_text,
            simulate=simulate,
            working_dir=working_dir,
            auto_confirm=True,
        )
        self._worker.log_message.connect(self._log_panel.append)
        self._worker.run_finished.connect(self._on_run_finished)
        self._worker.run_failed.connect(self._on_run_failed)
        self._worker.finished.connect(self._on_worker_thread_finished)
        self._worker.start()

    def stop_run(self) -> None:
        """Request the background worker to stop (best-effort)."""
        if self._worker is not None and self._worker.isRunning():
            self._log_panel.append(
                "Stop requested — waiting for the current operation to finish…",
                level="warn",
            )
            self._worker.requestInterruption()
            # QThread cannot forcibly kill Python code safely; user must wait.
            self._status_label.setText("Stop requested…")

    def _set_running(self, running: bool) -> None:
        """Enable/disable run-related actions based on worker state."""
        self.act_dry_run.setEnabled(not running)
        self.act_run.setEnabled(not running)
        self.act_stop.setEnabled(running)

    def _on_run_finished(self, success: int, errors: int) -> None:
        """Handle normal completion of a run."""
        self._status_label.setText(f"Done — success={success}, errors={errors}")
        self._set_running(False)

    def _on_run_failed(self, message: str) -> None:
        """Handle a failed run (parse or execution error)."""
        self._log_panel.append(message, level="error")
        self._status_label.setText("Run failed")
        self._set_running(False)
        QMessageBox.critical(self, "Run failed", message)

    def _on_worker_thread_finished(self) -> None:
        """Clean up after the worker thread fully exits."""
        self._set_running(False)
        self._worker = None

    # ------------------------------------------------------------------
    # Rule list / editor events
    # ------------------------------------------------------------------

    def _on_rule_selected(self, index: int) -> None:
        """Load the selected rule into the editor."""
        rules = self._document.rules
        if 0 <= index < len(rules):
            self._rule_editor.set_rule(rules[index])
        else:
            self._rule_editor.set_rule(None)

    def _on_rules_modified(self) -> None:
        """Handle structural changes to the rule list."""
        self._mark_dirty()

    def _on_rule_changed(self) -> None:
        """Handle edits inside the rule editor."""
        self._rule_list.refresh_current_label()
        self._mark_dirty()

    # ------------------------------------------------------------------
    # Misc
    # ------------------------------------------------------------------

    def show_about(self) -> None:
        """Show a short about dialog."""
        QMessageBox.about(
            self,
            "About organize GUI",
            "<h3>organize — Rule Editor</h3>"
            "<p>Interactive GUI for creating, editing and running "
            "<b>organize</b> file-management rules.</p>"
            "<p>Use <b>Dry-run</b> to simulate changes safely before a live "
            "<b>Run</b>. Logs and errors appear in the bottom panel and can "
            "be saved to a file.</p>"
            "<p>Documentation: "
            "<a href='https://organize.readthedocs.io'>"
            "organize.readthedocs.io</a></p>",
        )

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802
        """Prompt to save and stop workers before closing."""
        if self._worker is not None and self._worker.isRunning():
            answer = QMessageBox.question(
                self,
                "Run in progress",
                "A run is still in progress. Quit anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
                event.ignore()
                return
            self._worker.requestInterruption()
            # Wait briefly so the thread can exit cleanly and restore cwd.
            if not self._worker.wait(5000):
                self._log_panel.append(
                    "Worker still running after stop request; quitting anyway.",
                    level="warn",
                )
        if not self._confirm_discard():
            event.ignore()
            return
        event.accept()
