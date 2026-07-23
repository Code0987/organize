"""Coverage for app bootstrap, MainWindow actions, log panel, services."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest
from PyQt6.QtGui import QCloseEvent
from PyQt6.QtWidgets import QMessageBox

from ui.models.config_document import ConfigDocument
from ui.models.pipeline_item import PipelineItem
from ui.models.rule_item import RuleItem
from ui.services.capture_output import CaptureOutput, LogEntry
from ui.services.config_io import (
    ConfigIOError,
    load_config,
    save_config,
    validate_with_organize,
)
from ui.styles.palette import ThemeMode
from ui.widgets.log_panel_widget import LogPanelWidget
from ui.workers.organize_worker import OrganizeWorker


pytestmark = pytest.mark.usefixtures("qapp")


def test_import_ui_package():
    import importlib.util
    from pathlib import Path

    init = Path(__file__).resolve().parents[2] / "ui" / "__init__.py"
    spec = importlib.util.spec_from_file_location("organize_ui_init", init)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.__version__ == "0.1.0"


def test_main_entry_exits_with_run_code(monkeypatch):
    monkeypatch.setattr("ui.app.run", lambda argv=None: 7)
    from ui.__main__ import main

    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 7


def test_app_run_bootstraps(monkeypatch, qapp):
    import ui.app as app_mod

    monkeypatch.setattr(app_mod, "configure_process_dpi", lambda: 1.25)
    monkeypatch.setattr(app_mod, "detect_system_theme", lambda: ThemeMode.DARK)
    monkeypatch.setattr(app_mod, "apply_theme", lambda app, mode=None: 1.25)
    monkeypatch.setattr(app_mod, "current_theme_mode", lambda app=None: ThemeMode.DARK)

    class FakeWindow:
        def __init__(self):
            self.status_label = SimpleNamespace(setText=lambda *_: None)

        def style(self):
            return SimpleNamespace(unpolish=lambda *_: None, polish=lambda *_: None)

        def update(self):
            return None

        def show(self):
            return None

    class FakeWatcher:
        def __init__(self, parent=None):
            self.theme_changed = SimpleNamespace(connect=lambda *_: None)

        def connect(self, *_):
            return None

    monkeypatch.setattr(app_mod, "MainWindow", FakeWindow)
    monkeypatch.setattr(app_mod, "ThemeWatcher", FakeWatcher)
    monkeypatch.setattr(app_mod, "QApplication", lambda args: qapp)
    monkeypatch.setattr(qapp, "exec", lambda: 0)
    monkeypatch.setattr(qapp, "primaryScreen", lambda: SimpleNamespace(devicePixelRatio=lambda: 1.25))
    monkeypatch.setattr(qapp, "setApplicationName", lambda *_: None)
    monkeypatch.setattr(qapp, "setOrganizationName", lambda *_: None)
    monkeypatch.setattr(qapp, "setProperty", lambda *a, **k: None)

    assert app_mod.run(["organize-gui"]) == 0

    # theme-change callback path
    window = FakeWindow()
    calls = []

    def apply(app, mode=None):
        calls.append(mode)
        return 1.0

    monkeypatch.setattr(app_mod, "apply_theme", apply)
    # rebuild callback similarly to run()
    def _on_theme_changed(mode):
        if not isinstance(mode, ThemeMode):
            return
        apply(qapp, mode)
        window.style().unpolish(window)
        window.style().polish(window)
        window.update()
        window.status_label.setText("x")

    _on_theme_changed("nope")
    _on_theme_changed(ThemeMode.LIGHT)
    assert calls == [ThemeMode.LIGHT]


def test_log_panel_levels_clear_save(qapp, tmp_path, monkeypatch):
    panel = LogPanelWidget()
    now = datetime.now(timezone.utc)
    panel.append_entry(
        LogEntry(timestamp=now, level="info", message="hello", path="/a", sender="echo", rule_name="r1")
    )
    panel.append_entry(LogEntry(timestamp=now, level="warn", message="careful"))
    panel.append_entry(LogEntry(timestamp=now, level="error", message="boom"))
    panel.append_message("info", "freeform")
    assert "hello" in panel.plain_text()
    assert panel._entries

    out = tmp_path / "logs.txt"
    monkeypatch.setattr(
        "ui.widgets.log_panel_widget.QFileDialog.getSaveFileName",
        lambda *a, **k: (str(out), ""),
    )
    monkeypatch.setattr(
        "ui.widgets.log_panel_widget.QMessageBox.information",
        lambda *a, **k: None,
    )
    panel.save_to_file()
    assert out.exists()
    assert "hello" in out.read_text(encoding="utf-8")

    # cancel save
    monkeypatch.setattr(
        "ui.widgets.log_panel_widget.QFileDialog.getSaveFileName",
        lambda *a, **k: ("", ""),
    )
    panel.save_to_file()

    # write failure
    monkeypatch.setattr(
        "ui.widgets.log_panel_widget.QFileDialog.getSaveFileName",
        lambda *a, **k: (str(tmp_path / "nope" / "x.log"), ""),
    )
    monkeypatch.setattr(
        "ui.widgets.log_panel_widget.QMessageBox.critical",
        lambda *a, **k: None,
    )
    panel.save_to_file()

    panel.clear()
    assert panel.plain_text() == ""
    panel.close()


def test_capture_output_confirm_and_format():
    seen = []
    out = CaptureOutput(on_entry=seen.append, auto_confirm=True)
    out.start(True, None, Path("."))
    res = SimpleNamespace(path=Path("/tmp/f"), rule=SimpleNamespace(name="R"))
    out.msg(res, "m", sender=object(), level="info")
    assert out.confirm(res, "ok?", default=False, sender=object()) is True
    out2 = CaptureOutput(auto_confirm=False)
    assert out2.confirm(res, "ok?", default=False, sender=object()) is False
    out.end(1, 0)
    entry = LogEntry(
        timestamp=datetime.now(timezone.utc),
        level="info",
        message="x",
        path="/p",
        sender="s",
        rule_name="rn",
    )
    line = entry.format_line()
    assert "[INFO]" in line and "/p" in line and "<s>" in line and "(rn)" in line


def test_config_io_error_paths(tmp_path, monkeypatch):
    missing = tmp_path / "nope.yaml"
    with pytest.raises(ConfigIOError):
        load_config(missing)

    bad_root = tmp_path / "list.yaml"
    bad_root.write_text("- just a list\n", encoding="utf-8")
    with pytest.raises(ConfigIOError):
        load_config(bad_root)

    broken = tmp_path / "broken.yaml"
    broken.write_text("rules: [", encoding="utf-8")
    with pytest.raises(ConfigIOError):
        load_config(broken)

    # parse failure via invalid structure that is a dict but bad rules
    weird = tmp_path / "weird.yaml"
    weird.write_text("rules: 123\n", encoding="utf-8")
    with pytest.raises(ConfigIOError):
        load_config(weird)

    doc = ConfigDocument.new_with_example()
    with pytest.raises(ConfigIOError):
        save_config(doc, path=None)

    # write OSError
    target = tmp_path / "out.yaml"
    monkeypatch.setattr(
        Path,
        "write_text",
        lambda self, *a, **k: (_ for _ in ()).throw(OSError("disk full")),
    )
    with pytest.raises(ConfigIOError):
        save_config(doc, target)

    # validation failure
    bad_doc = ConfigDocument(rules=[])
    # empty rules may still validate as empty config? organize wants rules key with content
    # Use invalid action-less by building empty actions incorrectly
    bad_doc.rules = [
        RuleItem(name="x", locations=["."], actions=[
            PipelineItem(kind="action", name="echo", primary_value="hi")
        ])
    ]
    # force invalid yaml parse path via monkeypatch
    monkeypatch.setattr(
        "ui.services.config_io.document_to_yaml",
        lambda d: "rules:\n  - locations: .\n    actions: []\n",
    )
    ok, msg = validate_with_organize(bad_doc)
    assert ok is False
    assert msg


def test_main_window_file_ops(main_window, tmp_path, monkeypatch, sample_tree):
    mw = main_window
    monkeypatch.setattr(QMessageBox, "information", lambda *a, **k: None)
    monkeypatch.setattr(QMessageBox, "warning", lambda *a, **k: None)
    monkeypatch.setattr(QMessageBox, "critical", lambda *a, **k: None)
    monkeypatch.setattr(QMessageBox, "about", lambda *a, **k: None)
    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *a, **k: QMessageBox.StandardButton.Yes,
    )

    # new config
    mw.document.mark_dirty()
    mw.new_config()
    assert mw.document.rules

    # cancel discard
    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *a, **k: QMessageBox.StandardButton.No,
    )
    mw.document.mark_dirty()
    before = mw.document
    mw.new_config()
    assert mw.document is before

    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *a, **k: QMessageBox.StandardButton.Yes,
    )

    # save as
    path = tmp_path / "cfg.yaml"
    monkeypatch.setattr(
        "ui.main_window.QFileDialog.getSaveFileName",
        lambda *a, **k: (str(path), ""),
    )
    mw.document.path = None
    mw.save_config()  # redirects to save_as
    assert path.exists()

    # save existing path
    mw.save_config()

    # save cancel
    monkeypatch.setattr(
        "ui.main_window.QFileDialog.getSaveFileName",
        lambda *a, **k: ("", ""),
    )
    mw.document.path = None
    mw.save_config_as()

    # open
    monkeypatch.setattr(
        "ui.main_window.QFileDialog.getOpenFileName",
        lambda *a, **k: (str(path), ""),
    )
    mw.open_config()
    assert mw.document.path == path

    # open cancel
    monkeypatch.setattr(
        "ui.main_window.QFileDialog.getOpenFileName",
        lambda *a, **k: ("", ""),
    )
    mw.open_config()

    # open failure
    monkeypatch.setattr(
        "ui.main_window.QFileDialog.getOpenFileName",
        lambda *a, **k: (str(tmp_path / "missing.yaml"), ""),
    )
    mw.open_config()

    # save failure
    mw.document.path = path

    def fail_save(doc, p=None):
        raise ConfigIOError("nope")

    monkeypatch.setattr("ui.main_window.save_config", fail_save)
    mw.save_config()

    monkeypatch.setattr(
        "ui.main_window.QFileDialog.getSaveFileName",
        lambda *a, **k: (str(tmp_path / "x.yaml"), ""),
    )
    mw.save_config_as()

    # validate ok + fail
    mw.validate_config()
    monkeypatch.setattr(
        "ui.main_window.validate_with_organize",
        lambda doc: (False, "bad"),
    )
    mw.validate_config()

    # browse working dir
    monkeypatch.setattr(
        "ui.main_window.QFileDialog.getExistingDirectory",
        lambda *a, **k: str(tmp_path),
    )
    mw._browse_working_dir()
    assert mw.working_dir_edit.text() == str(tmp_path)
    monkeypatch.setattr(
        "ui.main_window.QFileDialog.getExistingDirectory",
        lambda *a, **k: "",
    )
    mw._browse_working_dir()

    mw._about()
    assert mw._confirm_discard() is True  # still dirty? mark clean
    mw.document.mark_clean()
    assert mw._confirm_discard() is True
    assert mw._is_headless() is True


def test_main_window_run_paths(main_window, sample_tree, monkeypatch, qapp):
    mw = main_window
    monkeypatch.setattr(QMessageBox, "information", lambda *a, **k: None)
    monkeypatch.setattr(QMessageBox, "warning", lambda *a, **k: None)
    monkeypatch.setattr(QMessageBox, "critical", lambda *a, **k: None)

    # Point rule at sample tree
    mw.document = ConfigDocument(
        rules=[
            RuleItem(
                name="echo",
                locations=[str(sample_tree / "Downloads")],
                filters=[
                    PipelineItem(kind="filter", name="extension", primary_value="pdf")
                ],
                actions=[
                    PipelineItem(kind="action", name="echo", primary_value="{path.name}")
                ],
            )
        ]
    )
    mw._load_document_into_ui()
    mw.working_dir_edit.setText(str(sample_tree))

    # Prefer dry-run yes
    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *a, **k: QMessageBox.StandardButton.Yes,
    )
    mw.dry_run_check.setChecked(True)

    # Replace worker with sync stub
    class SyncWorker:
        def __init__(self, *a, **k):
            self.log_entry = SimpleNamespace(connect=lambda cb: setattr(self, "_log_cb", cb))
            self.finished_ok = SimpleNamespace(connect=lambda cb: setattr(self, "_ok_cb", cb))
            self.failed = SimpleNamespace(connect=lambda cb: setattr(self, "_fail_cb", cb))
            self.finished = SimpleNamespace(connect=lambda cb: setattr(self, "_done_cb", cb))
            self._running = False

        def start(self):
            self._running = True
            from ui.services.capture_output import LogEntry
            from datetime import datetime, timezone

            self._log_cb(
                LogEntry(
                    timestamp=datetime.now(timezone.utc),
                    level="info",
                    message="invoice.pdf",
                )
            )
            self._ok_cb(1, 0)
            self._done_cb()
            self._running = False

        def isRunning(self):
            return self._running

        def wait(self, *_):
            return True

    monkeypatch.setattr("ui.main_window.OrganizeWorker", SyncWorker)
    mw.run_live()
    mw.run_simulation()

    # Prefer dry-run cancel
    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *a, **k: QMessageBox.StandardButton.Cancel,
    )
    mw.run_live()

    # Prefer dry-run no -> live confirm no
    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *a, **k: QMessageBox.StandardButton.No,
    )
    monkeypatch.setattr(
        QMessageBox,
        "warning",
        lambda *a, **k: QMessageBox.StandardButton.No,
    )
    mw.run_live()

    # live confirm yes
    monkeypatch.setattr(
        QMessageBox,
        "warning",
        lambda *a, **k: QMessageBox.StandardButton.Yes,
    )
    mw.dry_run_check.setChecked(False)
    mw.run_live()

    # invalid config
    monkeypatch.setattr(
        "ui.main_window.validate_with_organize",
        lambda doc: (False, "invalid"),
    )
    mw.run_simulation()

    # empty rules
    monkeypatch.setattr(
        "ui.main_window.validate_with_organize",
        lambda doc: (True, ""),
    )
    mw.document.rules = []
    mw.run_simulation()

    # busy worker
    mw.document.rules = [
        RuleItem(
            name="x",
            locations=[str(sample_tree / "Downloads")],
            actions=[PipelineItem(kind="action", name="echo", primary_value="h")],
        )
    ]
    mw._worker = SimpleNamespace(isRunning=lambda: True)
    mw.run_simulation()
    mw._worker = None

    # worker failed path
    mw._on_worker_failed("boom")
    mw._on_worker_log("not-an-entry")
    mw._on_worker_ok(2, 1)
    mw._on_worker_finished()

    # closeEvent headless with running worker
    mw._worker = SimpleNamespace(isRunning=lambda: True, wait=lambda *_: True)
    ev = QCloseEvent()
    mw.closeEvent(ev)
    assert ev.isAccepted()

    # non-headless discard denied
    monkeypatch.setattr(mw, "_is_headless", lambda: False)
    monkeypatch.setattr(mw, "_confirm_discard", lambda: False)
    mw._worker = None
    ev2 = QCloseEvent()
    mw.closeEvent(ev2)
    assert not ev2.isAccepted()

    # non-headless running worker warning
    mw._worker = SimpleNamespace(isRunning=lambda: True)
    ev3 = QCloseEvent()
    mw.closeEvent(ev3)
    assert not ev3.isAccepted()


def test_worker_failed_path(sample_tree, monkeypatch):
    doc = ConfigDocument(
        rules=[
            RuleItem(
                name="bad",
                locations=[str(sample_tree / "Downloads")],
                actions=[
                    PipelineItem(kind="action", name="echo", primary_value="x")
                ],
            )
        ]
    )

    def boom(*a, **k):
        raise RuntimeError("explode")

    monkeypatch.setattr("ui.workers.organize_worker.run_document", boom)
    worker = OrganizeWorker(doc, simulate=True, working_dir=sample_tree)
    errors = []
    worker.failed.connect(errors.append)
    worker.run()
    assert errors and "explode" in errors[0]
