"""Organize Output implementation that forwards messages via callbacks.

This avoids QObject thread-affinity issues when organize runs inside a
:class:`~PyQt6.QtCore.QThread`. The worker wires callbacks to its own
Qt signals so the GUI thread can update widgets safely.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Callable, Optional

from organize.output._sender import sender_name
from organize.output.output import Level

if TYPE_CHECKING:
    from organize.resource import Resource
    from organize.output._sender import SenderType

# Callbacks: message(text, level), finished(success, errors)
MessageCallback = Callable[[str, str], None]
FinishedCallback = Callable[[int, int], None]


class CallbackOutput:
    """Organize ``Output`` protocol implementation using plain callbacks.

    Attributes:
        auto_confirm: Automatically answer yes to confirm actions.
    """

    def __init__(
        self,
        on_message: MessageCallback,
        on_finished: Optional[FinishedCallback] = None,
        *,
        auto_confirm: bool = True,
    ) -> None:
        """Initialize the callback output.

        Args:
            on_message: Called with ``(text, level)`` for each log line.
            on_finished: Optional callback with ``(success_count, error_count)``.
            auto_confirm: Automatically answer yes to confirm actions.
        """
        self._on_message = on_message
        self._on_finished = on_finished
        self.auto_confirm = auto_confirm
        self._last_rule_nr: Optional[int] = None
        self._last_path: Optional[Path] = None

    def start(
        self,
        simulate: bool,
        config_path: Optional[Path],
        working_dir: Path,
    ) -> None:
        """Called by organize when execution starts."""
        self._last_rule_nr = None
        self._last_path = None
        cfg = str(config_path) if config_path else "(in-memory)"
        mode = "SIMULATION (dry-run)" if simulate else "LIVE RUN"
        self._on_message(f"=== {mode} ===", "system")
        self._on_message(f"Working directory: {working_dir}", "system")
        self._on_message(f"Config: {cfg}", "system")

    def msg(
        self,
        res: "Resource",
        msg: str,
        sender: "SenderType",
        level: Level = "info",
    ) -> None:
        """Called by organize for each pipeline log line."""
        if res.rule_nr != self._last_rule_nr:
            self._last_rule_nr = res.rule_nr
            self._last_path = None
            rule_name = ""
            if res.rule is not None and res.rule.name:
                rule_name = f": {res.rule.name}"
            self._on_message(f"── Rule #{res.rule_nr}{rule_name} ──", "system")

        if res.path is not None and res.path != self._last_path:
            self._last_path = res.path
            basedir = f" (in {res.basedir})" if res.basedir else ""
            self._on_message(f"  {res.path}{basedir}", "info")

        src = sender_name(sender)
        prefix = "    " if res.path is not None else ""
        ui_level = "info"
        if level == "error":
            ui_level = "error"
            text = f"{prefix}[{src}] ERROR: {msg}"
        elif level == "warn":
            ui_level = "warn"
            text = f"{prefix}[{src}] {msg}"
        else:
            text = f"{prefix}[{src}] {msg}"
        self._on_message(text, ui_level)

    def confirm(
        self,
        res: "Resource",
        msg: str,
        default: bool,
        sender: "SenderType",
    ) -> bool:
        """Handle confirm actions; auto-confirms when configured."""
        src = sender_name(sender)
        path = str(res.path) if res.path else "(no path)"
        if self.auto_confirm:
            self._on_message(
                f"    [{src}] Confirm: {msg} → auto-yes ({path})",
                "warn",
            )
            return True
        self._on_message(
            f"    [{src}] Confirm: {msg} → using default={default} ({path})",
            "warn",
        )
        return default

    def end(self, success_count: int, error_count: int) -> None:
        """Called by organize when execution finishes."""
        if success_count == 0 and error_count == 0:
            self._on_message("Nothing to do.", "system")
        else:
            level = "success" if error_count == 0 else "warn"
            self._on_message(
                f"Finished: success={success_count}, errors={error_count}",
                level,
            )
        if self._on_finished is not None:
            self._on_finished(success_count, error_count)
