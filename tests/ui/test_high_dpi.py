"""Windows DPI parsing and scale snapping (no display required)."""

from ui.high_dpi import HighDpi


def test_parse_reg_dword() -> None:
    output = (
        "\nHKEY_CURRENT_USER\\Control Panel\\Desktop\n"
        "    LogPixels    REG_DWORD    0x78\n"
    )
    assert HighDpi.parse_reg_dword(output) == 120


def test_snap_common_windows_scales() -> None:
    assert HighDpi.snap(120 / 96) == 1.25
    assert HighDpi.snap(144 / 96) == 1.5
    assert HighDpi.snap(192 / 96) == 2.0
    assert HighDpi.snap(96 / 96) == 1.0


def test_apply_skips_offscreen(monkeypatch) -> None:
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    monkeypatch.delenv("QT_SCALE_FACTOR", raising=False)
    assert HighDpi().apply() == 1.0
    assert "QT_SCALE_FACTOR" not in __import__("os").environ
