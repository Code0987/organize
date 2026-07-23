"""Main application window for the organize desktop GUI."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QCloseEvent, QKeySequence
from PyQt6.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QFrame,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSplitter,
    QStatusBar,
    QTabWidget,
    QToolBar,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from ui.models.config_document import ConfigDocument
from ui.services.capture_output import LogEntry
from ui.services.config_io import (
    ConfigIOError,
    load_config,
    save_config,
    validate_with_organize,
)
from ui.widgets.log_panel_widget import LogPanelWidget
from ui.widgets.rule_editor_widget import RuleEditorWidget
from ui.widgets.rule_list_widget import RuleListWidget
from ui.widgets.yaml_preview_widget import YamlPreviewWidget
from ui.workers.organize_worker import OrganizeWorker


class MainWindow(QMainWindow):
    """Top-level window: rule list, editor, logs, dry-run / run controls."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Organize")
        self.resize(1280, 840)
        self.setMinimumSize(960, 640)
        # Ensure the window paints a solid background (no desktop bleed-through).
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setAutoFillBackground(True)

        self.document = ConfigDocument.new_with_example()
        self._worker: Optional[OrganizeWorker] = None
        self._suppress_dirty = False

        self._build_actions()
        self._build_toolbar()
        self._build_central()
        self._build_status()
        self._load_document_into_ui()
        self._update_title()

    # ----- construction -------------------------------------------------

    def _build_actions(self) -> None:
        self.act_new = QAction("New", self)
        self.act_new.setShortcut(QKeySequence.StandardKey.New)
        self.act_new.setToolTip("New configuration")
        self.act_new.triggered.connect(self.new_config)

        self.act_open = QAction("Open", self)
        self.act_open.setShortcut(QKeySequence.StandardKey.Open)
        self.act_open.setToolTip("Open YAML config")
        self.act_open.triggered.connect(self.open_config)

        self.act_save = QAction("Save", self)
        self.act_save.setShortcut(QKeySequence.StandardKey.Save)
        self.act_save.setToolTip("Save configuration")
        self.act_save.triggered.connect(self.save_config)

        self.act_save_as = QAction("Save as…", self)
        self.act_save_as.setShortcut(QKeySequence.StandardKey.SaveAs)
        self.act_save_as.triggered.connect(self.save_config_as)

        self.act_validate = QAction("Validate", self)
        self.act_validate.setToolTip("Check config with organize")
        self.act_validate.triggered.connect(self.validate_config)

        self.act_run = QAction("Run live", self)
        self.act_run.setToolTip("Apply rules for real (may change files)")
        self.act_run.triggered.connect(self.run_live)

        self.act_sim = QAction("Dry-run", self)
        self.act_sim.setShortcut(QKeySequence("Ctrl+R"))
        self.act_sim.setToolTip("Simulate without changing files (Ctrl+R)")
        self.act_sim.triggered.connect(self.run_simulation)

        self.act_quit = QAction("Quit", self)
        self.act_quit.setShortcut(QKeySequence.StandardKey.Quit)
        self.act_quit.triggered.connect(self.close)

        file_menu = self.menuBar().addMenu("&File")
        for action in (
            self.act_new,
            self.act_open,
            self.act_save,
            self.act_save_as,
        ):
            file_menu.addAction(action)
        file_menu.addSeparator()
        file_menu.addAction(self.act_quit)

        run_menu = self.menuBar().addMenu("&Run")
        run_menu.addAction(self.act_sim)
        run_menu.addAction(self.act_run)
        run_menu.addAction(self.act_validate)

        help_menu = self.menuBar().addMenu("&Help")
        about = QAction("About", self)
        about.triggered.connect(self._about)
        help_menu.addAction(about)

    def _build_toolbar(self) -> None:
        toolbar = QToolBar("Main")
        toolbar.setObjectName("MainToolbar")
        toolbar.setMovable(False)
        toolbar.setFloatable(False)
        toolbar.setIconSize(toolbar.iconSize())
        self.addToolBar(toolbar)

        for action in (self.act_new, self.act_open, self.act_save):
            toolbar.addAction(action)

        toolbar.addSeparator()
        toolbar.addAction(self.act_validate)

        toolbar.addSeparator()

        # Primary dry-run control as a styled tool button.
        self.sim_button = QToolButton()
        self.sim_button.setDefaultAction(self.act_sim)
        self.sim_button.setObjectName("PrimaryButton")
        self.sim_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        toolbar.addWidget(self.sim_button)

        self.run_button = QToolButton()
        self.run_button.setDefaultAction(self.act_run)
        self.run_button.setObjectName("DangerButton")
        self.run_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        toolbar.addWidget(self.run_button)

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        toolbar.addWidget(spacer)

        self.dry_run_check = QCheckBox("Prefer dry-run")
        self.dry_run_check.setChecked(True)
        self.dry_run_check.setToolTip(
            "When checked, Run live still asks for confirmation and "
            "defaults to safer behaviour in prompts."
        )
        toolbar.addWidget(self.dry_run_check)

        wd_label = QLabel("  Working dir")
        wd_label.setObjectName("HintLabel")
        toolbar.addWidget(wd_label)

        self.working_dir_edit = QLineEdit(str(Path.home()))
        self.working_dir_edit.setMinimumWidth(200)
        self.working_dir_edit.setMaximumWidth(320)
        self.working_dir_edit.setPlaceholderText("Working directory")
        toolbar.addWidget(self.working_dir_edit)

        browse = QPushButton("…")
        browse.setFixedWidth(36)
        browse.setCursor(Qt.CursorShape.PointingHandCursor)
        browse.setToolTip("Choose working directory")
        browse.clicked.connect(self._browse_working_dir)
        toolbar.addWidget(browse)

    def _build_central(self) -> None:
        central = QWidget()
        central.setObjectName("CentralRoot")
        central.setAutoFillBackground(True)
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        vertical = QSplitter(Qt.Orientation.Vertical)
        vertical.setChildrenCollapsible(False)
        vertical.setHandleWidth(8)

        horizontal = QSplitter(Qt.Orientation.Horizontal)
        horizontal.setChildrenCollapsible(False)
        horizontal.setHandleWidth(8)

        # Left sidebar
        side = QFrame()
        side.setObjectName("SidePanel")
        side_layout = QVBoxLayout(side)
        side_layout.setContentsMargins(12, 12, 12, 12)
        side_layout.setSpacing(8)
        self.rule_list = RuleListWidget()
        side_layout.addWidget(self.rule_list)
        side.setMinimumWidth(220)
        side.setMaximumWidth(360)
        horizontal.addWidget(side)

        # Center editor with tabs
        editor_panel = QFrame()
        editor_panel.setObjectName("EditorPanel")
        editor_layout = QVBoxLayout(editor_panel)
        editor_layout.setContentsMargins(12, 8, 12, 12)
        editor_layout.setSpacing(4)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)

        self.rule_editor = RuleEditorWidget()
        self.tabs.addTab(self.rule_editor, "Rule editor")

        self.yaml_preview = YamlPreviewWidget()
        self.tabs.addTab(self.yaml_preview, "YAML preview")

        editor_layout.addWidget(self.tabs)
        horizontal.addWidget(editor_panel)

        horizontal.setStretchFactor(0, 0)
        horizontal.setStretchFactor(1, 1)
        horizontal.setSizes([260, 900])

        vertical.addWidget(horizontal)

        log_frame = QFrame()
        log_frame.setObjectName("LogPanel")
        log_layout = QVBoxLayout(log_frame)
        log_layout.setContentsMargins(12, 12, 12, 12)
        self.log_panel = LogPanelWidget()
        log_layout.addWidget(self.log_panel)
        log_frame.setMinimumHeight(140)
        vertical.addWidget(log_frame)

        vertical.setStretchFactor(0, 5)
        vertical.setStretchFactor(1, 2)
        vertical.setSizes([620, 200])

        layout.addWidget(vertical)

        self.rule_list.selection_changed.connect(self._on_rule_selected)
        self.rule_list.changed.connect(self._on_document_changed)
        self.rule_editor.changed.connect(self._on_rule_edited)

    def _build_status(self) -> None:
        status = QStatusBar()
        self.setStatusBar(status)
        self.status_label = QLabel("Ready — edit a rule, then Dry-run to preview")
        status.addWidget(self.status_label, 1)

    # ----- document plumbing --------------------------------------------

    def _load_document_into_ui(self) -> None:
        self._suppress_dirty = True
        try:
            self.rule_list.set_rules(self.document.rules)
            if self.document.rules:
                self.rule_list.set_current_index(0)
                self.rule_editor.set_rule(self.document.rules[0])
            else:
                self.rule_editor.set_rule(None)
            self.yaml_preview.update_from_document(self.document)
        finally:
            self._suppress_dirty = False
        self._update_title()

    def _on_rule_selected(self, index: int) -> None:
        self.rule_editor.commit_to_rule()
        if index < 0 or index >= len(self.document.rules):
            self.rule_editor.set_rule(None)
            return
        self.rule_editor.set_rule(self.document.rules[index])

    def _on_rule_edited(self) -> None:
        self.rule_list.refresh_current_label()
        self._on_document_changed()

    def _on_document_changed(self) -> None:
        if self._suppress_dirty:
            return
        self.document.mark_dirty()
        self.yaml_preview.update_from_document(self.document)
        self._update_title()

    def _update_title(self) -> None:
        name = self.document.path.name if self.document.path else "Untitled"
        dirty = " •" if self.document.dirty else ""
        self.setWindowTitle(f"Organize — {name}{dirty}")

    def _confirm_discard(self) -> bool:
        if not self.document.dirty:
            return True
        answer = QMessageBox.question(
            self,
            "Unsaved changes",
            "You have unsaved changes. Discard them?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        return answer == QMessageBox.StandardButton.Yes

    # ----- file operations ----------------------------------------------

    def new_config(self) -> None:
        """Create a new example configuration."""
        if not self._confirm_discard():
            return
        self.document = ConfigDocument.new_with_example()
        self._load_document_into_ui()
        self.log_panel.append_message("info", "Created new configuration with example rule.")
        self.status_label.setText("New configuration")

    def open_config(self) -> None:
        """Open a YAML config from disk."""
        if not self._confirm_discard():
            return
        path_str, _ = QFileDialog.getOpenFileName(
            self,
            "Open organize config",
            str(Path.home()),
            "YAML files (*.yaml *.yml);;All files (*)",
        )
        if not path_str:
            return
        path = Path(path_str)
        try:
            self.document = load_config(path)
        except ConfigIOError as exc:
            QMessageBox.critical(self, "Open failed", str(exc))
            return
        self._load_document_into_ui()
        self.log_panel.append_message("info", f"Opened {path}")
        self.status_label.setText(f"Opened {path.name}")

    def save_config(self) -> None:
        """Save to the current path, or prompt if none."""
        self.rule_editor.commit_to_rule()
        if self.document.path is None:
            self.save_config_as()
            return
        try:
            save_config(self.document)
        except ConfigIOError as exc:
            QMessageBox.critical(self, "Save failed", str(exc))
            return
        self._update_title()
        self.status_label.setText(f"Saved {self.document.path}")
        self.log_panel.append_message("info", f"Saved {self.document.path}")

    def save_config_as(self) -> None:
        """Prompt for a path and save."""
        self.rule_editor.commit_to_rule()
        path_str, _ = QFileDialog.getSaveFileName(
            self,
            "Save organize config",
            str(self.document.path or Path.home() / "config.yaml"),
            "YAML files (*.yaml *.yml);;All files (*)",
        )
        if not path_str:
            return
        path = Path(path_str)
        try:
            save_config(self.document, path)
        except ConfigIOError as exc:
            QMessageBox.critical(self, "Save failed", str(exc))
            return
        self._update_title()
        self.status_label.setText(f"Saved {path}")
        self.log_panel.append_message("info", f"Saved {path}")

    def validate_config(self) -> None:
        """Validate the current document with organize's parser."""
        self.rule_editor.commit_to_rule()
        ok, message = validate_with_organize(self.document)
        if ok:
            self.status_label.setText("Config is valid")
            self.log_panel.append_message("info", "Validation OK.")
            QMessageBox.information(self, "Validation", "Configuration is valid.")
        else:
            self.status_label.setText("Config invalid")
            self.log_panel.append_message("error", f"Validation failed: {message}")
            QMessageBox.warning(self, "Validation failed", message)

    # ----- run / simulate -----------------------------------------------

    def _browse_working_dir(self) -> None:
        path = QFileDialog.getExistingDirectory(
            self, "Working directory", self.working_dir_edit.text()
        )
        if path:
            self.working_dir_edit.setText(path)

    def run_simulation(self) -> None:
        """Always run in dry-run mode."""
        self._start_worker(simulate=True)

    def run_live(self) -> None:
        """Run live with a strong confirmation prompt."""
        if self.dry_run_check.isChecked():
            # Safer default path when prefer dry-run is on.
            answer = QMessageBox.question(
                self,
                "Dry-run preferred",
                "“Prefer dry-run” is enabled.\n\n"
                "Run a safe dry-run instead of a live run?",
                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.No
                | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Yes,
            )
            if answer == QMessageBox.StandardButton.Cancel:
                return
            if answer == QMessageBox.StandardButton.Yes:
                self._start_worker(simulate=True)
                return

        answer = QMessageBox.warning(
            self,
            "Live run",
            "This will apply actions for real.\n"
            "Files may be moved, renamed, or deleted.\n\n"
            "Continue with a LIVE run?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        self._start_worker(simulate=False)

    def _start_worker(self, *, simulate: bool) -> None:
        if self._worker is not None and self._worker.isRunning():
            QMessageBox.information(
                self, "Busy", "A run is already in progress. Please wait."
            )
            return

        self.rule_editor.commit_to_rule()
        ok, message = validate_with_organize(self.document)
        if not ok:
            QMessageBox.warning(
                self,
                "Invalid configuration",
                f"Fix validation errors before running:\n\n{message}",
            )
            self.log_panel.append_message("error", f"Validation failed: {message}")
            return

        if not self.document.rules:
            QMessageBox.information(self, "No rules", "Add at least one rule first.")
            return

        work = Path(self.working_dir_edit.text().strip() or ".").expanduser()
        mode = "Dry-run" if simulate else "LIVE run"
        self.log_panel.append_message("info", f"—— {mode} started ——")
        self.status_label.setText(f"{mode} running…")
        self._set_run_actions_enabled(False)

        self._worker = OrganizeWorker(
            self.document,
            simulate=simulate,
            working_dir=work,
            parent=self,
        )
        self._worker.log_entry.connect(self._on_worker_log)
        self._worker.finished_ok.connect(self._on_worker_ok)
        self._worker.failed.connect(self._on_worker_failed)
        self._worker.finished.connect(self._on_worker_finished)
        self._worker.start()

    def _on_worker_log(self, entry: object) -> None:
        if isinstance(entry, LogEntry):
            self.log_panel.append_entry(entry)

    def _on_worker_ok(self, success_count: int, error_count: int) -> None:
        self.status_label.setText(
            f"Done — successes={success_count}, errors={error_count}"
        )
        self.log_panel.append_message(
            "info",
            f"—— Finished: successes={success_count}, errors={error_count} ——",
        )

    def _on_worker_failed(self, message: str) -> None:
        self.status_label.setText("Run failed")
        self.log_panel.append_message("error", f"Run failed: {message}")
        QMessageBox.critical(self, "Run failed", message)

    def _on_worker_finished(self) -> None:
        self._set_run_actions_enabled(True)
        self._worker = None

    def _set_run_actions_enabled(self, enabled: bool) -> None:
        self.act_run.setEnabled(enabled)
        self.act_sim.setEnabled(enabled)
        self.act_validate.setEnabled(enabled)

    # ----- misc ---------------------------------------------------------

    def _about(self) -> None:
        QMessageBox.about(
            self,
            "About Organize",
            "<b>Organize</b> desktop UI<br><br>"
            "Create and edit rules interactively, dry-run them safely, "
            "inspect activity logs, and export standard organize YAML.",
        )

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802
        if self._worker is not None and self._worker.isRunning():
            # Headless / automated runs cannot dismiss modal dialogs.
            if self._is_headless():
                self._worker.wait(1000)
                event.accept()
                return
            QMessageBox.warning(
                self,
                "Run in progress",
                "Please wait for the current run to finish before closing.",
            )
            event.ignore()
            return
        if not self._is_headless() and not self._confirm_discard():
            event.ignore()
            return
        event.accept()

    @staticmethod
    def _is_headless() -> bool:
        """True when running under offscreen/minimal Qt platforms (tests/CI)."""
        import os

        platform = (os.environ.get("QT_QPA_PLATFORM") or "").lower()
        return platform in {"offscreen", "minimal", "null"}
