"""Tests for LogPanel buffer and save behaviour."""

from __future__ import annotations

from pathlib import Path

import pytest

from organize_gui.widgets.log_panel import LogPanel


@pytest.fixture()
def log_panel(qapp):
    panel = LogPanel()
    yield panel
    panel.close()
    panel.deleteLater()


class TestLogPanel:
    def test_append_and_clear(self, log_panel) -> None:
        log_panel.append("hello", level="info")
        log_panel.append("boom", level="error")
        text = log_panel.text()
        assert "hello" in text
        assert "boom" in text
        log_panel.clear()
        assert log_panel.text() == ""

    def test_save_logs_writes_file(self, log_panel, tmp_path: Path, monkeypatch) -> None:
        from PyQt6.QtWidgets import QFileDialog

        target = tmp_path / "out.txt"
        log_panel.append("line one", level="info")
        log_panel.append("line two", level="warn")

        monkeypatch.setattr(
            QFileDialog,
            "getSaveFileName",
            lambda *a, **k: (str(target), "Text files (*.txt)"),
        )
        log_panel.save_logs()
        assert target.is_file()
        content = target.read_text(encoding="utf-8")
        assert "line one" in content
        assert "line two" in content
