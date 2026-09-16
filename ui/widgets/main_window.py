"""Main application window: configs, interactive rules, dry-run, logs."""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Set

from PyQt6.QtCore import QSettings, Qt, QUrl
from PyQt6.QtGui import QAction, QCloseEvent, QDesktopServices
from PyQt6.QtWidgets import (
    QDialog,
    QFileDialog,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QStatusBar,
    QTabWidget,
    QWidget,
)

from organize.errors import ConfigError
from organize.find_config import example_config_path

from ui import ORGANIZE_VERSION
from ui.constants import APP_NAME, DOCS_URL, ORG_NAME, SETTINGS_KEY_LAST_CONFIG
from ui.models.config_document import ConfigDocument
from ui.models.rule_factory import RuleFactory
from ui.models.run_request import RunRequest
from ui.runner.organize_worker import OrganizeWorker
from ui.widgets.app_icon import AppIcon
from ui.widgets.log_panel import LogPanel
from ui.widgets.main_toolbar import MainToolbar
from ui.widgets.new_config_dialog import NewConfigDialog
from ui.widgets.rule_workspace import RuleWorkspace
from ui.widgets.sidebar import Sidebar


class MainWindow(QMainWindow):
    """Top-level window that wires the sidebar, editor, and log panel."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("organize")
        self.setWindowIcon(AppIcon().build())
        self.resize(1280, 820)

        self.settings = QSettings(ORG_NAME, APP_NAME)
        self.document = ConfigDocument.blank()
        self.factory = RuleFactory()
        self.worker: Optional[OrganizeWorker] = None

        self.sidebar = Sidebar()
        self.sidebar.new_requested.connect(self.new_config)
        self.sidebar.browse_requested.connect(self.open_config)
        self.sidebar.open_requested.connect(self.open_path)

        self.rule_workspace = RuleWorkspace()
        self.rule_workspace.rules_changed.connect(self._on_rules_changed)
        self.logs = LogPanel()

        self.tabs = QTabWidget()
        self.tabs.addTab(self.rule_workspace, "Rules")
        self.tabs.addTab(self.logs, "Logs")

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self.sidebar)
        splitter.addWidget(self.tabs)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([260, 1020])
        self.setCentralWidget(splitter)

        self.toolbar = MainToolbar(self)
        self.addToolBar(self.toolbar)
        self.toolbar.check_requested.connect(self.check_config)
        self.toolbar.dry_run_requested.connect(self.dry_run)
        self.toolbar.run_requested.connect(self.run_config)

        self._build_menus()
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self._refresh_sidebar()
        self._load_document(self.document, status="New unsaved config")
        self._restore_last()

    def _build_menus(self) -> None:
        file_menu = self.menuBar().addMenu("&File")
        file_menu.addAction(self._action("&New…", self.new_config, "Ctrl+N"))
        file_menu.addAction(self._action("&Open…", self.open_config, "Ctrl+O"))
        file_menu.addAction(self._action("&Save", self.save_config, "Ctrl+S"))
        file_menu.addAction(self._action("Save &As…", self.save_config_as, "Ctrl+Shift+S"))
        file_menu.addSeparator()
        file_menu.addAction(self._action("Save &log…", self.logs.save_log))
        file_menu.addAction(self._action("Save &errors…", self.logs.save_errors))
        file_menu.addSeparator()
        file_menu.addAction(self._action("E&xit", self.close, "Ctrl+Q"))

        run_menu = self.menuBar().addMenu("&Run")
        run_menu.addAction(self._action("&Check", self.check_config, "Ctrl+L"))
        run_menu.addAction(self._action("&Dry run", self.dry_run, "Ctrl+R"))
        run_menu.addAction(self._action("R&un", self.run_config, "Ctrl+Return"))

        help_menu = self.menuBar().addMenu("&Help")
        help_menu.addAction(self._action("organize &Documentation", self.open_docs))
        help_menu.addAction(self._action("&About", self.show_about))

    def _action(
        self,
        text: str,
        slot: object,
        shortcut: Optional[str] = None,
    ) -> QAction:
        action = QAction(text, self)
        if shortcut:
            action.setShortcut(shortcut)
        action.triggered.connect(slot)
        return action

    def _refresh_sidebar(self) -> None:
        self.sidebar.set_configs(self.factory.discovered_configs(), self.document.path)

    def _load_document(self, document: ConfigDocument, status: str) -> None:
        self.document = document
        try:
            self.rule_workspace.set_rules(document.rules())
        except ValueError:
            pass
        self._update_title()
        self.status.showMessage(status, 4000)
        self._refresh_sidebar()
        if document.path:
            self.settings.setValue(SETTINGS_KEY_LAST_CONFIG, str(document.path))

    def _update_title(self) -> None:
        dirty = " •" if self.document.dirty else ""
        name = self.document.display_name
        self.toolbar.set_title(f"{name}{dirty}")
        self.setWindowTitle(f"{name}{dirty} — organize")

    def _on_rules_changed(self, rules: list) -> None:
        self.document.set_rules(rules)
        self._update_title()

    def _confirm_discard(self) -> bool:
        if not self.document.dirty:
            return True
        choice = QMessageBox.question(
            self,
            "Unsaved changes",
            "Save changes to the current config?",
            QMessageBox.StandardButton.Save
            | QMessageBox.StandardButton.Discard
            | QMessageBox.StandardButton.Cancel,
        )
        if choice == QMessageBox.StandardButton.Cancel:
            return False
        if choice == QMessageBox.StandardButton.Save:
            return self.save_config()
        return True

    def new_config(self) -> None:
        """Create a config from a preset."""
        if not self._confirm_discard():
            return
        dialog = NewConfigDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted or dialog.preset is None:
            return
        self._load_document(
            ConfigDocument.blank(dialog.preset),
            status=f"Started from “{dialog.preset.title}”",
        )
        self.document.dirty = True
        self._update_title()

    def open_config(self) -> None:
        """Open a YAML config from a file dialog."""
        if not self._confirm_discard():
            return
        start = self.document.path.parent if self.document.path else Path.home()
        path, _filter = QFileDialog.getOpenFileName(
            self,
            "Open organize config",
            str(start),
            "YAML (*.yaml *.yml);;All files (*)",
        )
        if path:
            self.open_path(Path(path))

    def open_path(self, path: Path) -> None:
        """Open ``path`` if it is not already the current document."""
        if self.document.path and path.resolve() == self.document.path.resolve():
            return
        if not self._confirm_discard():
            return
        try:
            document = ConfigDocument.from_path(path)
        except OSError as exc:
            QMessageBox.critical(self, "Could not open", str(exc))
            return
        self._load_document(document, status=f"Opened {path}")

    def save_config(self) -> bool:
        """Save to the current path, or ask for one."""
        if self.document.path is None:
            return self.save_config_as()
        try:
            self.document.save()
        except OSError as exc:
            QMessageBox.critical(self, "Could not save", str(exc))
            return False
        self._update_title()
        self.status.showMessage(f"Saved {self.document.path}", 4000)
        self._refresh_sidebar()
        return True

    def save_config_as(self) -> bool:
        """Save the current config under a new path."""
        suggested = example_config_path(None)
        path, _filter = QFileDialog.getSaveFileName(
            self,
            "Save organize config",
            str(self.document.path or suggested),
            "YAML (*.yaml *.yml);;All files (*)",
        )
        if not path:
            return False
        target = Path(path)
        if target.suffix.lower() not in {".yaml", ".yml"}:
            target = target.with_suffix(".yaml")
        try:
            self.document.save(target)
        except OSError as exc:
            QMessageBox.critical(self, "Could not save", str(exc))
            return False
        self._update_title()
        self.status.showMessage(f"Saved {target}", 4000)
        self._refresh_sidebar()
        return True

    def check_config(self) -> None:
        """Validate the current rules with organize's Config loader."""
        try:
            config = self.document.validate()
        except (ConfigError, ValueError, Exception) as exc:
            QMessageBox.warning(self, "Config problem", str(exc))
            self.status.showMessage("Config has errors", 4000)
            return
        QMessageBox.information(
            self,
            "Config is valid",
            f"{len(config.rules)} rule(s) parsed successfully.",
        )
        self.status.showMessage("Config is valid", 4000)

    def _parse_tags(self, text: str) -> Set[str]:
        return {part.strip() for part in text.split(",") if part.strip()}

    def dry_run(self) -> None:
        """Simulate the current rules without writing to disk."""
        self._start_run(simulate=True)

    def run_config(self) -> None:
        """Apply the current rules after an explicit confirmation."""
        confirm = QMessageBox.warning(
            self,
            "Run organize",
            "This will change files on disk according to the current rules.\n\n"
            "Use Dry run first if you have not already. Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return
        self._start_run(simulate=False)

    def _start_run(self, simulate: bool) -> None:
        if self.worker is not None and self.worker.isRunning():
            QMessageBox.information(self, "Busy", "A run is already in progress.")
            return
        try:
            self.document.validate()
        except Exception as exc:  # noqa: BLE001
            QMessageBox.warning(self, "Config problem", str(exc))
            return

        working = self.toolbar.working_directory()
        request = RunRequest(
            text=self.document.text,
            config_path=self.document.path,
            simulate=simulate,
            working_dir=working,
            tags=self._parse_tags(self.toolbar.tags()),
            skip_tags=self._parse_tags(self.toolbar.skip_tags()),
        )
        self.tabs.setCurrentWidget(self.logs)
        self.logs.reset(simulate=simulate, working_dir=str(working))
        self.worker = OrganizeWorker(request, self)
        self.worker.started_run.connect(self._on_started)
        self.worker.message.connect(self.logs.add_message)
        self.worker.finished_run.connect(self._on_finished)
        self.worker.failed.connect(self._on_failed)
        self.worker.confirm_requested.connect(
            self._on_confirm, Qt.ConnectionType.QueuedConnection
        )
        self.status.showMessage("Dry run…" if simulate else "Organizing…")
        self.worker.start()

    def _on_started(self, simulate: bool, config_path: str, working_dir: str) -> None:
        mode = "Dry run" if simulate else "Run"
        extra = f"  ·  {config_path}" if config_path else ""
        self.status.showMessage(f"{mode} started in {working_dir}{extra}")

    def _on_finished(self, success: int, errors: int) -> None:
        self.logs.finish(success, errors)
        self.status.showMessage(f"Done — success {success} / fail {errors}", 8000)

    def _on_failed(self, message: str) -> None:
        self.logs.fail(message)
        self.status.showMessage("Run failed", 6000)
        QMessageBox.critical(self, "Run failed", message)

    def _on_confirm(self, box: dict) -> None:
        path = box.get("path") or ""
        prompt = box.get("msg") or "Continue?"
        if path:
            prompt = f"{prompt}\n\n{path}"
        default_btn = (
            QMessageBox.StandardButton.Yes
            if box.get("default", True)
            else QMessageBox.StandardButton.No
        )
        answer = QMessageBox.question(
            self,
            "Confirm",
            prompt,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            default_btn,
        )
        box["result"] = answer == QMessageBox.StandardButton.Yes
        box["event"].set()

    def open_docs(self) -> None:
        """Open the official organize documentation in a browser."""
        QDesktopServices.openUrl(QUrl(DOCS_URL))

    def show_about(self) -> None:
        """Show version and a short description."""
        QMessageBox.about(
            self,
            "About organize",
            f"<b>organize</b> v{ORGANIZE_VERSION}<br><br>"
            "Create, edit, and run file-organization rules.<br>"
            "Dry run previews changes; Run applies them.<br><br>"
            f'<a href="{DOCS_URL}">{DOCS_URL}</a>',
        )

    def _restore_last(self) -> None:
        last = self.settings.value(SETTINGS_KEY_LAST_CONFIG)
        if not last:
            return
        path = Path(str(last))
        if path.is_file():
            try:
                self._load_document(
                    ConfigDocument.from_path(path), status=f"Opened {path}"
                )
            except OSError:
                pass

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802
        if self.worker is not None and self.worker.isRunning():
            QMessageBox.information(
                self, "Busy", "Wait for the current run to finish before quitting."
            )
            event.ignore()
            return
        if not self._confirm_discard():
            event.ignore()
            return
        event.accept()
