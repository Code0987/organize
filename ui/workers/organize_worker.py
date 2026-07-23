"""Background QThread worker that runs organize without blocking the UI."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from PyQt6.QtCore import QThread, pyqtSignal

from ui.models.config_document import ConfigDocument
from ui.services.capture_output import LogEntry
from ui.services.runner import run_document


class OrganizeWorker(QThread):
    """Execute an organize config on a worker thread.

    Signals:
        log_entry: Emitted for each captured log line.
        finished_ok: Emitted with (success_count, error_count) on success.
        failed: Emitted with an error message if execution raises.
    """

    log_entry = pyqtSignal(object)
    finished_ok = pyqtSignal(int, int)
    failed = pyqtSignal(str)

    def __init__(
        self,
        document: ConfigDocument,
        *,
        simulate: bool,
        working_dir: Optional[Path] = None,
        parent: Optional[object] = None,
    ) -> None:
        super().__init__(parent)  # type: ignore[arg-type]
        self._document = document.clone()
        self._simulate = simulate
        self._working_dir = working_dir

    def run(self) -> None:
        """Thread entry point."""
        try:
            output = run_document(
                self._document,
                simulate=self._simulate,
                working_dir=self._working_dir,
                on_entry=self._forward_entry,
                auto_confirm=True,
            )
            self.finished_ok.emit(output.success_count, output.error_count)
        except Exception as exc:  # noqa: BLE001 - surface to UI
            self.failed.emit(str(exc))

    def _forward_entry(self, entry: LogEntry) -> None:
        self.log_entry.emit(entry)
