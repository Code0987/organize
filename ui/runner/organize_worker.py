"""QThread that runs ``Config.execute`` without freezing the GUI."""

from __future__ import annotations

import logging
import os
from typing import Optional

from PyQt6.QtCore import QObject, QThread, pyqtSignal

from organize import Config

from ui.models.config_document import ConfigDocument
from ui.models.location_preflight import LocationPreflight
from ui.models.run_request import RunRequest
from ui.runner.worker_output import WorkerOutput


class OrganizeWorker(QThread):
    """Execute one organize config on a background thread.

    Signals:
        started_run: ``(simulate, config_path, working_dir)``
        message: dict payload for the log panel
        finished_run: ``(success_count, error_count)``
        failed: exception string
        confirm_requested: mutable dict the GUI fills in
    """

    started_run = pyqtSignal(bool, str, str)
    message = pyqtSignal(dict)
    finished_run = pyqtSignal(int, int)
    failed = pyqtSignal(str)
    confirm_requested = pyqtSignal(object)

    def __init__(
        self,
        request: RunRequest,
        parent: Optional[QObject] = None,
    ) -> None:
        super().__init__(parent)
        self.request = request

    def run(self) -> None:
        """Parse the config, execute it, then restore the process cwd."""
        previous_cwd = os.getcwd()
        # Per-file template errors are already sent to the log panel; a
        # traceback for every file would flood stderr and look like a crash.
        logging.getLogger("organize").setLevel(logging.CRITICAL)
        try:
            config = Config.from_string(
                config=self.request.text,
                config_path=self.request.config_path,
            )
            output = WorkerOutput(self)
            self._emit_preflight()
            config.execute(
                simulate=self.request.simulate,
                output=output,
                tags=self.request.tags,
                skip_tags=self.request.skip_tags,
                working_dir=self.request.working_dir,
            )
        except Exception as exc:  # noqa: BLE001 - surface any failure in the UI
            self.failed.emit(str(exc))
        finally:
            try:
                os.chdir(previous_cwd)
            except OSError:
                pass

    def _emit_preflight(self) -> None:
        """Warn about missing or empty locations before organize walks them."""
        try:
            rules = ConfigDocument(text=self.request.text).rules()
        except ValueError:
            return
        preflight = LocationPreflight()
        for check in preflight.inspect_rules(rules):
            self.message.emit(
                {
                    "level": check.level,
                    "path": str(check.resolved),
                    "basedir": "",
                    "sender": "preflight",
                    "msg": check.message,
                    "rule_nr": 0,
                    "rule_name": check.rule_name,
                }
            )
