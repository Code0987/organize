"""Organize Output implementation that records messages for the GUI."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, List, Optional

from organize.output.output import Level
from organize.resource import Resource

from organize.output._sender import sender_name


LogCallback = Callable[["LogEntry"], None]


@dataclass
class LogEntry:
    """A single log line captured during a run/simulation.

    Attributes:
        timestamp: UTC time when the entry was recorded.
        level: Organize message level (info / warn / error) or meta levels.
        message: Human-readable text.
        path: Related file path, if any.
        sender: Filter/action/rule sender name.
        rule_name: Rule that produced the message.
    """

    timestamp: datetime
    level: str
    message: str
    path: Optional[str] = None
    sender: str = ""
    rule_name: str = ""

    def format_line(self) -> str:
        """Format this entry as a single plain-text log line."""
        ts = self.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        parts = [f"[{ts}]", f"[{self.level.upper()}]"]
        if self.rule_name:
            parts.append(f"({self.rule_name})")
        if self.sender:
            parts.append(f"<{self.sender}>")
        if self.path:
            parts.append(self.path)
        parts.append(self.message)
        return " ".join(parts)


@dataclass
class CaptureOutput:
    """Collect organize pipeline messages without printing to the terminal.

    Confirmation prompts are auto-accepted so the GUI worker does not block
    on stdin. Users can rely on dry-run mode to inspect behaviour safely.
    """

    on_entry: Optional[LogCallback] = None
    auto_confirm: bool = True
    entries: List[LogEntry] = field(default_factory=list)
    success_count: int = 0
    error_count: int = 0

    def _emit(
        self,
        level: str,
        message: str,
        *,
        path: Optional[str] = None,
        sender: str = "",
        rule_name: str = "",
    ) -> None:
        entry = LogEntry(
            timestamp=datetime.now(timezone.utc),
            level=level,
            message=message,
            path=path,
            sender=sender,
            rule_name=rule_name,
        )
        self.entries.append(entry)
        if self.on_entry is not None:
            self.on_entry(entry)

    def start(
        self,
        simulate: bool,
        config_path: Optional[Path],
        working_dir: Path,
    ) -> None:
        mode = "simulation (dry-run)" if simulate else "LIVE run"
        cfg = str(config_path) if config_path else "(in-memory)"
        self._emit(
            "info",
            f"Starting {mode} | config={cfg} | working_dir={working_dir}",
        )

    def msg(
        self,
        res: Resource,
        msg: str,
        sender: object,
        level: Level = "info",
    ) -> None:
        rule_name = ""
        if res.rule is not None and res.rule.name:
            rule_name = res.rule.name
        self._emit(
            level,
            msg,
            path=str(res.path) if res.path else None,
            sender=sender_name(sender),
            rule_name=rule_name,
        )

    def confirm(
        self,
        res: Resource,
        msg: str,
        default: bool,
        sender: object,
    ) -> bool:
        rule_name = ""
        if res.rule is not None and res.rule.name:
            rule_name = res.rule.name
        decision = True if self.auto_confirm else default
        self._emit(
            "warn",
            f"Confirm '{msg}' -> {'yes' if decision else 'no'} (auto)",
            path=str(res.path) if res.path else None,
            sender=sender_name(sender),
            rule_name=rule_name,
        )
        return decision

    def end(self, success_count: int, error_count: int) -> None:
        self.success_count = success_count
        self.error_count = error_count
        self._emit(
            "info",
            f"Finished. successes={success_count}, errors={error_count}",
        )
