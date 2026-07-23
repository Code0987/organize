import subprocess
from datetime import datetime, timedelta, timezone

import pytest
from arrow import now as arrow_now

from organize.filters import Created
from organize.filters.created import read_created, read_stat_created


def test_min():
    now = arrow_now()
    ct = Created(days=10, hours=12, mode="older")
    assert not ct.matches_datetime(now - timedelta(days=10, hours=0))
    assert ct.matches_datetime(now - timedelta(days=10, hours=13))


def test_max():
    now = arrow_now()
    ct = Created(days=10, hours=12, mode="newer")
    assert ct.matches_datetime(now - timedelta(days=10, hours=0))
    assert not ct.matches_datetime(now - timedelta(days=10, hours=13))


def test_read_created(tmp_path):
    f = tmp_path / "file.txt"
    f.touch()
    try:
        created = read_created(f)
    except EnvironmentError:
        # Birth/creation time is not available on every OS/filesystem.
        pytest.skip("File creation time is not available on this platform")
    # Compare as UTC dates so local/UTC midnight edge cases are consistent.
    assert created.date() == datetime.now(timezone.utc).date()


def test_read_stat_created_rejects_epoch_zero(monkeypatch, tmp_path):
    """GNU stat returns 0 when birth time is unknown; that must not be used."""
    f = tmp_path / "file.txt"
    f.touch()

    def fake_check_output(cmd, encoding="utf-8"):
        # Simulate GNU stat --format=%W returning "0" (unknown).
        if "--format=%W" in cmd:
            return "0\n"
        raise subprocess.CalledProcessError(1, cmd)

    monkeypatch.setattr(subprocess, "check_output", fake_check_output)
    assert read_stat_created(f) is None
