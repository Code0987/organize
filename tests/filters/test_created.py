from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from arrow import now as arrow_now

from organize.filters import Created
from organize.filters.created import _valid_timestamp, read_created, read_stat_created


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
    assert read_created(f).date() == datetime.now(timezone.utc).date()


def test_unknown_birth_time_is_invalid():
    assert _valid_timestamp(0) is None
    assert _valid_timestamp(0.0) is None
    assert _valid_timestamp("0") is None
    assert _valid_timestamp(-1) is None
    assert _valid_timestamp(None) is None
    assert _valid_timestamp("not-a-date") is None
    assert _valid_timestamp(1_700_000_000) == 1_700_000_000.0


def test_read_created_falls_back_when_birth_time_unknown(tmp_path, monkeypatch):
    f = tmp_path / "file.txt"
    f.touch()
    real_stat = f.stat()

    def fake_stat(_self, *args, **kwargs):
        return SimpleNamespace(st_ctime=real_stat.st_ctime, st_mtime=real_stat.st_mtime)

    monkeypatch.setattr(type(f), "stat", fake_stat)
    monkeypatch.setattr(
        "organize.filters.created.read_stat_created", lambda _path: None
    )

    created = read_created(f)
    assert created.date() == datetime.fromtimestamp(
        real_stat.st_ctime, timezone.utc
    ).date()
    assert created.year != 1970 or created.month != 1 or created.day != 1


def test_read_stat_created_ignores_gnu_unknown(tmp_path, monkeypatch):
    f = tmp_path / "file.txt"
    f.touch()

    def fake_check_output(cmd, *args, **kwargs):
        if any(isinstance(part, str) and "%W" in part for part in cmd):
            return "0\n"
        raise FileNotFoundError(cmd)

    monkeypatch.setattr(
        "organize.filters.created.subprocess.check_output", fake_check_output
    )
    monkeypatch.setattr("organize.filters.created.sys.platform", "linux")
    assert read_stat_created(f) is None
