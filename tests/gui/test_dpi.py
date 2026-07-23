"""Tests for high-DPI stylesheet scaling helpers."""


from ui.styles.dpi import _clamp_scale, scale_stylesheet, sp


def test_sp_scales_and_rounds():
    assert sp(10, 1.0) == 10
    assert sp(10, 1.5) == 15
    assert sp(10, 1.25) == 12
    assert sp(1, 0.5) == 1  # never below 1


def test_scale_stylesheet_replaces_px_tokens():
    src = "padding: 8px; border-radius: 12.5px; color: red;"
    out = scale_stylesheet(src, 2.0)
    assert "padding: 16px;" in out
    assert "border-radius: 25px;" in out
    assert "color: red;" in out


def test_scale_stylesheet_noop_at_one():
    src = "padding: 8px;"
    assert scale_stylesheet(src, 1.0) == src


def test_clamp_scale():
    assert _clamp_scale(0.1) == 0.75
    assert _clamp_scale(10) == 4.0
    assert _clamp_scale(1.25) == 1.25


def test_detect_windows_scale_if_available():
    # Should not crash; may return None outside Windows/WSL.
    from ui.styles.dpi import detect_host_scale_factor

    value = detect_host_scale_factor()
    if value is not None:
        assert 0.75 <= value <= 4.0
