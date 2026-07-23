"""Broad unit coverage for DPI + system theme helpers (mocked host probes)."""

from __future__ import annotations

import os
import subprocess
from types import SimpleNamespace

import pytest

import ui.styles.dpi as dpi
from ui.styles.palette import ThemeMode
from ui.styles.system_theme import (
    ThemeWatcher,
    _find_powershell,
    _gnome_prefers_dark,
    _macos_prefers_dark,
    _windows_apps_use_light_theme,
    detect_system_theme,
)


@pytest.fixture(autouse=True)
def _reset_dpi_state(monkeypatch):
    """Keep DPI module state isolated per test."""
    monkeypatch.delenv("ORGANIZE_SKIP_HOST_PROBES", raising=False)
    # Leave QT_SCALE_FACTOR control to each test.
    dpi._INJECTED_QT_SCALE = None
    yield
    dpi._INJECTED_QT_SCALE = None


def test_configure_process_dpi_uses_organize_ui_scale(monkeypatch):
    monkeypatch.setenv("ORGANIZE_UI_SCALE", "1.5")
    monkeypatch.delenv("QT_SCALE_FACTOR", raising=False)
    monkeypatch.delenv("QT_FONT_DPI", raising=False)
    result = dpi.configure_process_dpi()
    assert result == pytest.approx(1.5)
    assert os.environ["QT_SCALE_FACTOR"] == "1.5"
    assert dpi._INJECTED_QT_SCALE == pytest.approx(1.5)
    assert dpi.screen_scale_factor() == pytest.approx(1.0)
    assert dpi.effective_ui_scale() == pytest.approx(1.5)


def test_configure_process_dpi_host_injection(monkeypatch):
    monkeypatch.delenv("ORGANIZE_UI_SCALE", raising=False)
    monkeypatch.delenv("QT_SCALE_FACTOR", raising=False)
    monkeypatch.setattr(dpi, "detect_host_scale_factor", lambda: 1.25)
    result = dpi.configure_process_dpi()
    assert result == pytest.approx(1.25)
    assert os.environ["QT_SCALE_FACTOR"] == "1.25"


def test_configure_process_dpi_no_host_scale(monkeypatch):
    monkeypatch.delenv("ORGANIZE_UI_SCALE", raising=False)
    monkeypatch.delenv("QT_SCALE_FACTOR", raising=False)
    monkeypatch.setattr(dpi, "detect_host_scale_factor", lambda: None)
    monkeypatch.setattr(dpi, "_enable_windows_dpi_awareness", lambda: None)
    assert dpi.configure_process_dpi() is None
    assert dpi._INJECTED_QT_SCALE is None


def test_detect_host_scale_skip_probes(monkeypatch):
    monkeypatch.setenv("ORGANIZE_SKIP_HOST_PROBES", "1")
    monkeypatch.setenv("ORGANIZE_UI_SCALE", "1.1")
    assert dpi.detect_host_scale_factor() == pytest.approx(1.1)
    monkeypatch.delenv("ORGANIZE_UI_SCALE", raising=False)
    monkeypatch.delenv("QT_SCALE_FACTOR", raising=False)
    assert dpi.detect_host_scale_factor() is None


def test_detect_host_scale_windows_and_gdk(monkeypatch):
    monkeypatch.delenv("ORGANIZE_SKIP_HOST_PROBES", raising=False)
    monkeypatch.delenv("ORGANIZE_UI_SCALE", raising=False)
    monkeypatch.delenv("QT_SCALE_FACTOR", raising=False)
    monkeypatch.setattr(dpi, "_windows_scale_factor", lambda: 1.5)
    assert dpi.detect_host_scale_factor() == pytest.approx(1.5)

    monkeypatch.setattr(dpi, "_windows_scale_factor", lambda: None)
    monkeypatch.setenv("GDK_SCALE", "2")
    assert dpi.detect_host_scale_factor() == pytest.approx(2.0)

    monkeypatch.delenv("GDK_SCALE", raising=False)
    assert dpi.detect_host_scale_factor() is None


def test_windows_scale_factor_from_powershell(monkeypatch):
    # On real Windows CI, native ctypes DPI is preferred; force the PowerShell path.
    monkeypatch.setattr(dpi, "_windows_scale_via_ctypes", lambda: None)
    monkeypatch.setattr(dpi, "_find_powershell", lambda: "powershell.exe")
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *a, **k: SimpleNamespace(stdout="144\n", returncode=0),
    )
    assert dpi._windows_scale_factor() == pytest.approx(1.5)

    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *a, **k: SimpleNamespace(stdout="not-a-number\n", returncode=0),
    )
    assert dpi._windows_scale_factor() is None

    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *a, **k: SimpleNamespace(stdout="50\n", returncode=0),
    )
    assert dpi._windows_scale_factor() is None

    def boom(*a, **k):
        raise OSError("nope")

    monkeypatch.setattr(subprocess, "run", boom)
    assert dpi._windows_scale_factor() is None

    monkeypatch.setattr(dpi, "_find_powershell", lambda: None)
    assert dpi._windows_scale_factor() is None





def test_windows_scale_via_ctypes_paths(monkeypatch):
    """Cover ctypes DPI helpers with a temporary fake ctypes package."""
    import sys
    import types

    real = sys.modules.get("ctypes")
    real_wt = sys.modules.get("ctypes.wintypes")

    def install(mode: str):
        mod = types.ModuleType("ctypes")

        def GetDpiForSystem():
            if mode == "system":
                return 120
            raise AttributeError("missing")

        def GetDC(_hdc):
            if mode == "caps":
                return 1
            raise OSError("no")

        def ReleaseDC(*args):
            return 0

        def GetDeviceCaps(*args):
            return 144

        def SetProcessDpiAwarenessContext(*args):
            raise OSError("fail")

        def SetProcessDpiAwareness(*args):
            raise OSError("fail")

        def SetProcessDPIAware():
            return True

        user32 = types.SimpleNamespace(
            GetDpiForSystem=GetDpiForSystem,
            GetDC=GetDC,
            ReleaseDC=ReleaseDC,
            SetProcessDpiAwarenessContext=SetProcessDpiAwarenessContext,
            SetProcessDPIAware=SetProcessDPIAware,
        )
        gdi32 = types.SimpleNamespace(GetDeviceCaps=GetDeviceCaps)
        shcore = types.SimpleNamespace(SetProcessDpiAwareness=SetProcessDpiAwareness)
        mod.windll = types.SimpleNamespace(user32=user32, gdi32=gdi32, shcore=shcore)
        mod.c_void_p = lambda x: x
        wt = types.ModuleType("ctypes.wintypes")
        wt.UINT = int
        mod.wintypes = wt
        sys.modules["ctypes"] = mod
        sys.modules["ctypes.wintypes"] = wt

    try:
        install("system")
        assert dpi._windows_scale_via_ctypes() == pytest.approx(1.25)
        install("caps")
        assert dpi._windows_scale_via_ctypes() == pytest.approx(1.5)
        install("fail")
        assert dpi._windows_scale_via_ctypes() is None
        dpi._enable_windows_dpi_awareness()
    finally:
        if real is not None:
            sys.modules["ctypes"] = real
        else:
            sys.modules.pop("ctypes", None)
        if real_wt is not None:
            sys.modules["ctypes.wintypes"] = real_wt
        else:
            sys.modules.pop("ctypes.wintypes", None)


def test_find_powershell(monkeypatch, tmp_path):
    monkeypatch.setattr(dpi.os.path, "isfile", lambda p: False)
    monkeypatch.setattr("shutil.which", lambda name: None)
    assert dpi._find_powershell() is None

    ps = tmp_path / "powershell.exe"
    # absolute path candidate in list is hard-coded; use which
    monkeypatch.setattr("shutil.which", lambda name: str(ps) if name == "pwsh" else None)
    assert dpi._find_powershell() == str(ps)

    monkeypatch.setattr(dpi.os.path, "isfile", lambda p: p.endswith("powershell.exe"))
    # first absolute candidate hits
    found = dpi._find_powershell()
    assert found is not None


def test_parse_format_helpers():
    assert dpi._parse_positive_float(None) is None
    assert dpi._parse_positive_float("") is None
    assert dpi._parse_positive_float("x") is None
    assert dpi._parse_positive_float("0") is None
    assert dpi._parse_positive_float("-1") is None
    assert dpi._parse_positive_float("1.25") == pytest.approx(1.25)
    assert dpi._format_scale(1.25) == "1.25"
    assert dpi._format_scale(1.0) == "1"
    assert dpi._clamp_scale(0.1) == 0.75
    assert dpi._clamp_scale(9) == 4.0


def test_screen_scale_without_injection(monkeypatch, qapp):
    dpi._INJECTED_QT_SCALE = None
    monkeypatch.delenv("QT_SCALE_FACTOR", raising=False)
    factor = dpi.screen_scale_factor(qapp)
    assert 0.75 <= factor <= 4.0
    assert dpi.effective_ui_scale(qapp) >= 1.0


def test_detect_system_theme_qt_scheme(monkeypatch, qapp):
    monkeypatch.delenv("ORGANIZE_THEME", raising=False)
    monkeypatch.delenv("ORGANIZE_SKIP_HOST_PROBES", raising=False)
    monkeypatch.setattr(
        "ui.styles.system_theme._windows_apps_use_light_theme", lambda: None
    )
    monkeypatch.setattr("ui.styles.system_theme._gnome_prefers_dark", lambda: None)

    from PyQt6.QtCore import Qt

    class Hints:
        def colorScheme(self):
            return Qt.ColorScheme.Dark

    monkeypatch.setattr(qapp, "styleHints", lambda: Hints())
    assert detect_system_theme() is ThemeMode.DARK

    class HintsLight:
        def colorScheme(self):
            return Qt.ColorScheme.Light

    monkeypatch.setattr(qapp, "styleHints", lambda: HintsLight())
    assert detect_system_theme() is ThemeMode.LIGHT


def test_detect_system_theme_windows_gnome_mac(monkeypatch):
    monkeypatch.delenv("ORGANIZE_THEME", raising=False)
    monkeypatch.delenv("ORGANIZE_SKIP_HOST_PROBES", raising=False)
    monkeypatch.setattr(
        "ui.styles.system_theme.QApplication.instance", lambda: None
    )
    monkeypatch.setattr(
        "ui.styles.system_theme.QGuiApplication.instance", lambda: None
    )

    monkeypatch.setattr(
        "ui.styles.system_theme._windows_apps_use_light_theme", lambda: False
    )
    assert detect_system_theme() is ThemeMode.DARK
    monkeypatch.setattr(
        "ui.styles.system_theme._windows_apps_use_light_theme", lambda: True
    )
    assert detect_system_theme() is ThemeMode.LIGHT

    monkeypatch.setattr(
        "ui.styles.system_theme._windows_apps_use_light_theme", lambda: None
    )
    monkeypatch.setattr("ui.styles.system_theme._gnome_prefers_dark", lambda: True)
    assert detect_system_theme() is ThemeMode.DARK
    monkeypatch.setattr("ui.styles.system_theme._gnome_prefers_dark", lambda: False)
    assert detect_system_theme() is ThemeMode.LIGHT

    monkeypatch.setattr("ui.styles.system_theme._gnome_prefers_dark", lambda: None)
    monkeypatch.setattr("ui.styles.system_theme.sys.platform", "darwin")
    monkeypatch.setattr("ui.styles.system_theme._macos_prefers_dark", lambda: True)
    assert detect_system_theme() is ThemeMode.DARK
    monkeypatch.setattr("ui.styles.system_theme._macos_prefers_dark", lambda: False)
    assert detect_system_theme() is ThemeMode.LIGHT
    monkeypatch.setattr("ui.styles.system_theme._macos_prefers_dark", lambda: None)
    assert detect_system_theme() is ThemeMode.LIGHT


def test_windows_apps_use_light_theme_powershell(monkeypatch):
    monkeypatch.setattr("ui.styles.system_theme.sys.platform", "linux")
    monkeypatch.setattr(
        "ui.styles.system_theme._find_powershell", lambda: "powershell.exe"
    )
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *a, **k: SimpleNamespace(stdout="0\n", returncode=0),
    )
    assert _windows_apps_use_light_theme() is False
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *a, **k: SimpleNamespace(stdout="1\n", returncode=0),
    )
    assert _windows_apps_use_light_theme() is True
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *a, **k: SimpleNamespace(stdout="unknown\n", returncode=0),
    )
    assert _windows_apps_use_light_theme() is None

    def boom(*a, **k):
        raise OSError("x")

    monkeypatch.setattr(subprocess, "run", boom)
    assert _windows_apps_use_light_theme() is None
    monkeypatch.setattr("ui.styles.system_theme._find_powershell", lambda: None)
    assert _windows_apps_use_light_theme() is None


def test_gnome_and_macos_helpers(monkeypatch):
    monkeypatch.setattr("ui.styles.system_theme.which", lambda name: None)
    assert _gnome_prefers_dark() is None

    monkeypatch.setattr("ui.styles.system_theme.which", lambda name: "gsettings")
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *a, **k: SimpleNamespace(
            stdout="'prefer-dark'", returncode=0
        ),
    )
    assert _gnome_prefers_dark() is True

    calls = {"n": 0}

    def run_side_effect(*a, **k):
        calls["n"] += 1
        if calls["n"] == 1:
            return SimpleNamespace(stdout="'default'", returncode=0)
        return SimpleNamespace(stdout="'Adwaita-dark'", returncode=0)

    monkeypatch.setattr(subprocess, "run", run_side_effect)
    assert _gnome_prefers_dark() is True

    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *a, **k: SimpleNamespace(stdout="'prefer-light'", returncode=0),
    )
    assert _gnome_prefers_dark() is False

    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *a, **k: (_ for _ in ()).throw(OSError("x")),
    )
    assert _gnome_prefers_dark() is None

    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *a, **k: SimpleNamespace(stdout="Dark\n", returncode=0),
    )
    assert _macos_prefers_dark() is True
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *a, **k: SimpleNamespace(stdout="", returncode=1),
    )
    assert _macos_prefers_dark() is False
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *a, **k: (_ for _ in ()).throw(OSError("x")),
    )
    assert _macos_prefers_dark() is None


def test_theme_watcher_emits_on_change(monkeypatch, qapp):
    monkeypatch.setenv("ORGANIZE_THEME", "light")
    watcher = ThemeWatcher(qapp)
    watcher._timer.stop()
    seen = []
    watcher.theme_changed.connect(seen.append)
    monkeypatch.setenv("ORGANIZE_THEME", "dark")
    watcher._recompute()
    assert seen == [ThemeMode.DARK]
    assert watcher.current is ThemeMode.DARK
    # no emit when unchanged
    watcher._recompute()
    assert seen == [ThemeMode.DARK]
    watcher._on_qt_scheme_changed(None)
    watcher._poll()
