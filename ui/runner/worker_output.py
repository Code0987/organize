"""organize ``Output`` adapter that talks to a Qt worker thread."""

from __future__ import annotations

import threading
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Optional

from organize.output._sender import SenderType, sender_name
from organize.output.output import Level
from organize.resource import Resource

if TYPE_CHECKING:
    from ui.runner.organize_worker import OrganizeWorker


class WorkerOutput:
    """Implements organize's Output protocol for the desktop runner.

    Messages are forwarded as Qt signals. ``confirm`` blocks the worker
    until the GUI thread writes a result onto the shared box.
    """

    def __init__(self, worker: "OrganizeWorker") -> None:
        self.worker = worker

    def start(
        self,
        simulate: bool,
        config_path: Optional[Path],
        working_dir: Path,
    ) -> None:
        """Notify the UI that a run has begun."""
        self.worker.started_run.emit(
            simulate,
            str(config_path) if config_path else "",
            str(working_dir),
        )

    def msg(
        self,
        res: Resource,
        msg: str,
        sender: SenderType,
        level: Level = "info",
    ) -> None:
        """Forward a pipeline message to the log panel."""
        payload: Dict[str, Any] = {
            "level": level,
            "path": str(res.path) if res.path else "",
            "basedir": str(res.basedir) if res.basedir else "",
            "sender": sender_name(sender),
            "msg": msg,
            "rule_nr": res.rule_nr,
            "rule_name": res.rule.name if res.rule and res.rule.name else "",
        }
        self.worker.message.emit(payload)

    def confirm(
        self,
        res: Resource,
        msg: str,
        default: bool,
        sender: SenderType,
    ) -> bool:
        """Ask the GUI thread for a yes/no answer and wait for it."""
        box: Dict[str, Any] = {
            "msg": msg,
            "default": default,
            "path": str(res.path) if res.path else "",
            "result": default,
            "event": threading.Event(),
        }
        self.worker.confirm_requested.emit(box)
        box["event"].wait()
        return bool(box["result"])

    def end(self, success_count: int, error_count: int) -> None:
        """Notify the UI that the run finished."""
        self.worker.finished_run.emit(success_count, error_count)
