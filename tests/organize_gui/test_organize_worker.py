"""Tests for OrganizeWorker dry-run execution and lifecycle."""

from __future__ import annotations

import os
from pathlib import Path
from typing import List, Tuple

import pytest

from organize_gui.workers.organize_worker import OrganizeWorker


def _make_echo_config(location: Path) -> str:
    """Build a tiny config that echoes PDF names under *location*."""
    loc = location.as_posix()
    return f"""
rules:
  - name: echo pdfs
    locations: "{loc}"
    filters:
      - extension: pdf
    actions:
      - echo: "PDF {{path.name}}"
"""


class TestOrganizeWorkerDryRun:
    def test_dry_run_emits_success_and_logs(
        self, qapp, tmp_path: Path
    ) -> None:
        (tmp_path / "a.pdf").write_text("x", encoding="utf-8")
        (tmp_path / "b.txt").write_text("y", encoding="utf-8")
        conf = _make_echo_config(tmp_path)

        logs: List[Tuple[str, str]] = []
        results: List[Tuple[str, object]] = []

        worker = OrganizeWorker(conf, simulate=True, working_dir=str(tmp_path))
        worker.log_message.connect(lambda text, level: logs.append((level, text)))
        worker.run_finished.connect(
            lambda s, e: results.append(("finished", s, e))
        )
        worker.run_failed.connect(lambda m: results.append(("failed", m)))

        # Run synchronously in this thread (avoids needing event-loop delivery)
        worker.run()

        assert results, "expected run_finished or run_failed"
        assert results[0][0] == "finished"
        assert results[0][1] >= 1  # success count
        assert results[0][2] == 0  # errors
        assert any("PDF a.pdf" in text for _, text in logs)
        assert any("SIMULATION" in text for _, text in logs)

    def test_invalid_config_emits_run_failed(self, qapp) -> None:
        worker = OrganizeWorker("not: valid: yaml: [", simulate=True)
        results: List[Tuple[str, object]] = []
        worker.run_failed.connect(lambda m: results.append(("failed", m)))
        worker.run_finished.connect(
            lambda s, e: results.append(("finished", s, e))
        )
        worker.run()
        assert results
        assert results[0][0] == "failed"
        assert "fail" in str(results[0][1]).lower() or "error" in str(
            results[0][1]
        ).lower() or "Configuration" in str(results[0][1])

    def test_cwd_restored_after_run(self, qapp, tmp_path: Path) -> None:
        (tmp_path / "a.pdf").write_text("x", encoding="utf-8")
        before = Path.cwd()
        worker = OrganizeWorker(
            _make_echo_config(tmp_path),
            simulate=True,
            working_dir=str(tmp_path),
        )
        worker.run()
        assert Path.cwd() == before

    def test_live_run_moves_file(self, qapp, tmp_path: Path) -> None:
        src = tmp_path / "inbox"
        dst = tmp_path / "out"
        src.mkdir()
        dst.mkdir()
        (src / "doc.pdf").write_text("data", encoding="utf-8")
        conf = f"""
rules:
  - locations: "{src.as_posix()}"
    filters:
      - extension: pdf
    actions:
      - move: "{dst.as_posix()}/"
"""
        worker = OrganizeWorker(conf, simulate=False, working_dir=str(tmp_path))
        finished: List[Tuple[int, int]] = []
        worker.run_finished.connect(lambda s, e: finished.append((s, e)))
        worker.run()
        assert finished
        assert finished[0][0] >= 1
        assert not (src / "doc.pdf").exists()
        assert (dst / "doc.pdf").exists()

    def test_dry_run_does_not_move_file(self, qapp, tmp_path: Path) -> None:
        src = tmp_path / "inbox"
        dst = tmp_path / "out"
        src.mkdir()
        dst.mkdir()
        (src / "doc.pdf").write_text("data", encoding="utf-8")
        conf = f"""
rules:
  - locations: "{src.as_posix()}"
    filters:
      - extension: pdf
    actions:
      - move: "{dst.as_posix()}/"
"""
        worker = OrganizeWorker(conf, simulate=True, working_dir=str(tmp_path))
        worker.run()
        assert (src / "doc.pdf").exists()
        assert not (dst / "doc.pdf").exists()


class TestOrganizeWorkerFailureSignals:
    """Review issue #4: do not emit both finished and failed for one run."""

    def test_execution_error_does_not_double_emit_finished_and_failed(
        self, qapp, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """If execute raises after end(), only one terminal outcome should win.

        Desired contract: either run_finished XOR run_failed for a given run,
        not both (which would flash Done and then an error dialog).
        """
        conf = f"""
rules:
  - locations: "{tmp_path.as_posix()}"
    actions:
      - echo: "hi"
"""

        def boom(self, config, output):  # type: ignore[no-untyped-def]
            # Mimic organize's pattern: end() in finally, then a raised error.
            try:
                raise RuntimeError("simulated execution failure")
            finally:
                output.end(0, 0)

        monkeypatch.setattr(OrganizeWorker, "_execute", boom)

        worker = OrganizeWorker(conf, simulate=True, working_dir=str(tmp_path))
        events: List[str] = []
        worker.run_finished.connect(lambda s, e: events.append("finished"))
        worker.run_failed.connect(lambda m: events.append("failed"))
        worker.run()

        # Desired: only one terminal signal
        assert events.count("finished") + events.count("failed") == 1, events
        assert "failed" in events


class TestOrganizeWorkerInterruption:
    """Review issue #2: Stop should be honoured by the worker."""

    def test_run_checks_interruption_request(
        self, qapp, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """When interruption is requested before/during execute, run should stop.

        This test simulates an interruption flag set before execute and expects
        the worker to exit without reporting a normal multi-file success path
        once interruption support is implemented.
        """
        # Create many files so a cooperative cancel has something to interrupt
        for i in range(20):
            (tmp_path / f"f{i}.pdf").write_text("x", encoding="utf-8")

        conf = _make_echo_config(tmp_path)
        worker = OrganizeWorker(conf, simulate=True, working_dir=str(tmp_path))

        # Force isInterruptionRequested to True for the duration of run()
        monkeypatch.setattr(worker, "isInterruptionRequested", lambda: True)

        logs: List[str] = []
        worker.log_message.connect(lambda text, level: logs.append(text))
        finished: List[Tuple[int, int]] = []
        failed: List[str] = []
        worker.run_finished.connect(lambda s, e: finished.append((s, e)))
        worker.run_failed.connect(lambda m: failed.append(m))
        worker.run()

        # Without interruption support the worker processes every file (success=20).
        # With support it must stop early (success < 20).
        if not finished:
            raise AssertionError(f"expected run_finished; failed={failed!r} logs={logs!r}")
        success, errors = finished[0]
        if success >= 20:
            raise AssertionError(
                f"interruption ignored: processed all files success={success} errors={errors}"
            )
