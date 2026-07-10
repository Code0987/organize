"""Tests for CallbackOutput (organize Output protocol bridge)."""

from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

from organize.resource import Resource
from organize_gui.workers.signal_output import CallbackOutput


class TestCallbackOutput:
    def test_start_and_end_messages(self) -> None:
        messages: List[Tuple[str, str]] = []
        finished: List[Tuple[int, int]] = []

        out = CallbackOutput(
            on_message=lambda text, level: messages.append((level, text)),
            on_finished=lambda s, e: finished.append((s, e)),
        )
        out.start(simulate=True, config_path=None, working_dir=Path("."))
        out.end(success_count=2, error_count=1)

        levels = [m[0] for m in messages]
        assert "system" in levels
        assert any("SIMULATION" in m[1] for m in messages)
        assert finished == [(2, 1)]
        assert any("success=2" in m[1] for m in messages)

    def test_msg_groups_by_rule_and_path(self) -> None:
        messages: List[str] = []
        out = CallbackOutput(on_message=lambda text, level: messages.append(text))

        res = Resource(path=Path("/tmp/a.pdf"), basedir=Path("/tmp"), rule_nr=0)
        # minimal fake rule name via monkeypatch style: rule stays None
        out.msg(res=res, msg="hello", sender="echo", level="info")
        out.msg(res=res, msg="again", sender="echo", level="info")

        # Path announced once, then two messages
        assert any("a.pdf" in m for m in messages)
        assert sum(1 for m in messages if "hello" in m) == 1
        assert sum(1 for m in messages if "again" in m) == 1

    def test_error_level(self) -> None:
        messages: List[Tuple[str, str]] = []
        out = CallbackOutput(
            on_message=lambda text, level: messages.append((level, text))
        )
        res = Resource(path=Path("/tmp/x"), basedir=Path("/tmp"), rule_nr=0)
        out.msg(res=res, msg="boom", sender="move", level="error")
        assert any(level == "error" and "ERROR" in text for level, text in messages)

    def test_confirm_auto_yes(self) -> None:
        messages: List[str] = []
        out = CallbackOutput(
            on_message=lambda text, level: messages.append(text),
            auto_confirm=True,
        )
        res = Resource(path=Path("/tmp/x"), basedir=Path("/tmp"), rule_nr=0)
        assert out.confirm(res=res, msg="Delete?", default=False, sender="confirm") is True
        assert any("auto-yes" in m for m in messages)

    def test_confirm_uses_default_when_not_auto(self) -> None:
        out = CallbackOutput(
            on_message=lambda text, level: None,
            auto_confirm=False,
        )
        res = Resource(path=None, rule_nr=0)
        assert out.confirm(res=res, msg="?", default=True, sender="confirm") is True
        assert out.confirm(res=res, msg="?", default=False, sender="confirm") is False

    def test_end_nothing_to_do(self) -> None:
        messages: List[str] = []
        out = CallbackOutput(on_message=lambda text, level: messages.append(text))
        out.end(0, 0)
        assert any("Nothing to do" in m for m in messages)
