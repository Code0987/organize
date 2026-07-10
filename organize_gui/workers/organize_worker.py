"""Background worker that runs organize configs without blocking the UI."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional, Set, Tuple

from PyQt6.QtCore import QThread, pyqtSignal

from organize import Config, ConfigError
from organize.config import should_execute
from organize.template import render
from organize.utils import ReportSummary
from organize_gui.workers.signal_output import CallbackOutput


class OrganizeWorker(QThread):
    """QThread that executes an organize config string.

    Signals:
        log_message: Forwarded log line (text, level).
        run_finished: Emitted on normal completion (success, errors).
        run_failed: Emitted when configuration or execution setup fails.

    Only one of ``run_finished`` / ``run_failed`` is emitted per run.
    Cooperative cancellation is supported via :meth:`requestInterruption`
    (checked before the run and between rules).
    """

    log_message = pyqtSignal(str, str)
    run_finished = pyqtSignal(int, int)
    run_failed = pyqtSignal(str)

    def __init__(
        self,
        config_yaml: str,
        *,
        simulate: bool = True,
        working_dir: Optional[str] = None,
        tags: Optional[Set[str]] = None,
        skip_tags: Optional[Set[str]] = None,
        auto_confirm: bool = True,
        parent=None,
    ) -> None:
        """Initialize the worker with run parameters.

        Args:
            config_yaml: Full YAML configuration text.
            simulate: If True, dry-run (no file changes).
            working_dir: Working directory for path resolution.
            tags: Optional tags to include.
            skip_tags: Optional tags to skip.
            auto_confirm: Auto-answer confirmation prompts.
            parent: Optional Qt parent.
        """
        super().__init__(parent)
        self._config_yaml = config_yaml
        self._simulate = simulate
        self._working_dir = working_dir or "."
        self._tags = tags or set()
        self._skip_tags = skip_tags or set()
        self._auto_confirm = auto_confirm

    def run(self) -> None:
        """Parse and execute the configuration (runs in the worker thread)."""
        try:
            config = Config.from_string(config=self._config_yaml, config_path=None)
        except ConfigError as exc:
            self.run_failed.emit(f"Configuration error:\n{exc}")
            return
        except Exception as exc:  # noqa: BLE001
            self.run_failed.emit(f"Failed to parse configuration:\n{exc}")
            return

        # Decide the terminal signal here so we never emit both finished and failed
        # (Config.execute always calls output.end in a finally block).
        failure_message: Optional[str] = None
        success_count = 0
        error_count = 0

        output = CallbackOutput(
            on_message=lambda text, level: self.log_message.emit(text, level),
            on_finished=None,
            auto_confirm=self._auto_confirm,
        )

        previous_cwd = Path.cwd()
        try:
            if self.isInterruptionRequested():
                self.log_message.emit("Run cancelled (stop requested).", "warn")
            else:
                success_count, error_count = self._execute(
                    config=config,
                    output=output,
                )
        except Exception as exc:  # noqa: BLE001
            self.log_message.emit(f"Execution error: {exc}", "error")
            failure_message = str(exc)
        finally:
            try:
                os.chdir(previous_cwd)
            except OSError:
                pass

        if failure_message is not None:
            self.run_failed.emit(failure_message)
        else:
            self.run_finished.emit(success_count, error_count)

    def _execute(
        self,
        config: Config,
        output: CallbackOutput,
    ) -> Tuple[int, int]:
        """Run rules cooperatively, honouring interruption between rules.

        Returns:
            ``(success_count, error_count)`` summary for the run.
        """
        working_path = Path(render(str(self._working_dir)))
        os.chdir(working_path)

        output.start(
            simulate=self._simulate,
            config_path=config._config_path,
            working_dir=working_path,
        )

        summary = ReportSummary()
        try:
            for rule_nr, rule in enumerate(config.rules):
                if self.isInterruptionRequested():
                    self.log_message.emit("Run cancelled (stop requested).", "warn")
                    break

                if not should_execute(
                    rule_tags=rule.tags,
                    tags=self._tags,
                    skip_tags=self._skip_tags,
                ):
                    continue

                summary += rule.execute(
                    simulate=self._simulate,
                    output=output,
                    rule_nr=rule_nr,
                )
        finally:
            output.end(summary.success, summary.errors)

        return summary.success, summary.errors
