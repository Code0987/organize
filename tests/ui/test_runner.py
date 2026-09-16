"""Headless smoke tests for the PyQt6 runner and main window."""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import QEventLoop, QTimer
from PyQt6.QtWidgets import QApplication

from ui.models.run_request import RunRequest
from ui.runner.organize_worker import OrganizeWorker


@pytest.fixture(scope="module")
def qapp() -> QApplication:
    """Reuse a single offscreen QApplication for this module."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_worker_dry_run_echo(qapp: QApplication, tmp_path) -> None:
    (tmp_path / "hello.txt").write_text("hi", encoding="utf-8")
    request = RunRequest(
        text=f"""
rules:
  - name: Echo names
    locations: "{tmp_path}"
    filters:
      - name
    actions:
      - echo: "{{name}}"
""",
        config_path=None,
        simulate=True,
        working_dir=tmp_path,
        tags=set(),
        skip_tags=set(),
    )
    worker = OrganizeWorker(request)
    messages = []
    finished = []
    failed = []
    worker.message.connect(messages.append)
    worker.finished_run.connect(lambda success, errors: finished.append((success, errors)))
    worker.failed.connect(failed.append)

    loop = QEventLoop()
    worker.finished_run.connect(loop.quit)
    worker.failed.connect(loop.quit)
    QTimer.singleShot(15000, loop.quit)
    worker.start()
    loop.exec()
    worker.wait(2000)

    assert failed == []
    assert finished == [(1, 0)]
    assert any(event.get("msg") == "hello" for event in messages)


def test_main_window_constructs(qapp: QApplication) -> None:
    from ui.widgets.main_window import MainWindow

    window = MainWindow()
    assert window.document.text
    assert window.tabs.count() == 2
    assert window.tabs.tabText(0) == "Rules"
    assert window.tabs.tabText(1) == "Logs"
    window.close()
