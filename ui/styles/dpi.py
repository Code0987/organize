"""High-DPI / Windows display-scaling helpers for the organize GUI.

Under WSLg / RDP, Qt often reports ``devicePixelRatio == 1.0`` and
``logicalDpi == 96`` even when Windows display scaling is 125%/150%.
Style sheets also do not scale ``px`` values reliably.

Strategy:
1. Detect the *host* scale (Windows registry AppliedDPI, env overrides).
2. Set ``QT_SCALE_FACTOR`` **before** ``QApplication`` so Qt scales the UI.
3. Scale stylesheet lengths only when a global Qt scale factor is *not*
   already doing that job (avoids double-scaling).
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from typing import Optional

from PyQt6.QtGui import QGuiApplication
from PyQt6.QtWidgets import QApplication

# Set by configure_process_dpi() when we inject QT_SCALE_FACTOR ourselves.
_INJECTED_QT_SCALE: Optional[float] = None


def configure_process_dpi() -> Optional[float]:
    """Configure OS/Qt DPI behaviour **before** creating ``QApplication``.

    Returns the scale factor that was applied via ``QT_SCALE_FACTOR``, if any.
    """
    global _INJECTED_QT_SCALE

    os.environ.setdefault("QT_ENABLE_HIGHDPI_SCALING", "1")
    os.environ.setdefault("QT_AUTO_SCREEN_SCALE_FACTOR", "1")
    os.environ.setdefault("QT_SCALE_FACTOR_ROUNDING_POLICY", "PassThrough")

    if sys.platform == "win32":
        _enable_windows_dpi_awareness()

    # Explicit user override always wins.
    explicit = _parse_positive_float(
        os.environ.get("ORGANIZE_UI_SCALE") or os.environ.get("QT_SCALE_FACTOR")
    )
    if explicit is not None:
        # Only QT_SCALE_FACTOR — setting QT_FONT_DPI as well double-scales fonts.
        os.environ["QT_SCALE_FACTOR"] = _format_scale(explicit)
        os.environ.pop("QT_FONT_DPI", None)
        _INJECTED_QT_SCALE = explicit
        return explicit

    host = detect_host_scale_factor()
    if host is not None and host >= 1.05:
        # Only inject when the host is clearly scaled; leave true 100% alone.
        # Do NOT also set QT_FONT_DPI: combined with QT_SCALE_FACTOR it stacks
        # (e.g. 1.25 * 1.25 → ~1.56× and the UI becomes huge / blurry).
        os.environ["QT_SCALE_FACTOR"] = _format_scale(host)
        os.environ.pop("QT_FONT_DPI", None)
        _INJECTED_QT_SCALE = host
        return host

    _INJECTED_QT_SCALE = None
    return None


def detect_host_scale_factor() -> Optional[float]:
    """Best-effort detection of the OS / host display scale.

    Order:
    1. ``ORGANIZE_UI_SCALE`` / ``QT_SCALE_FACTOR`` (caller usually handles these)
    2. Windows ``AppliedDPI`` / ``LogPixels`` via PowerShell (WSL + native)
    3. ``GDK_SCALE`` if present
    """
    if os.environ.get("ORGANIZE_SKIP_HOST_PROBES") == "1":
        for key in ("ORGANIZE_UI_SCALE", "QT_SCALE_FACTOR"):
            value = _parse_positive_float(os.environ.get(key))
            if value is not None:
                return value
        return None

    for key in ("ORGANIZE_UI_SCALE", "QT_SCALE_FACTOR"):
        value = _parse_positive_float(os.environ.get(key))
        if value is not None:
            return value

    win = _windows_scale_factor()
    if win is not None:
        return win

    gdk = _parse_positive_float(os.environ.get("GDK_SCALE"))
    if gdk is not None:
        return gdk

    return None


def _windows_scale_factor() -> Optional[float]:
    """Read Windows display scaling (AppliedDPI / 96).

    Works from native Windows and from WSL when ``powershell.exe`` is on PATH.
    """
    # Native Windows first (no shell needed).
    if sys.platform == "win32":
        native = _windows_scale_via_ctypes()
        if native is not None:
            return native

    ps = _find_powershell()
    if ps is None:
        return None

    # AppliedDPI is the most reliable "effective" desktop DPI.
    script = (
        "$m = Get-ItemProperty -Path 'HKCU:\\Control Panel\\Desktop\\WindowMetrics' "
        "-ErrorAction SilentlyContinue; "
        "$d = Get-ItemProperty -Path 'HKCU:\\Control Panel\\Desktop' "
        "-ErrorAction SilentlyContinue; "
        "if ($m -and $m.AppliedDPI) { [int]$m.AppliedDPI } "
        "elseif ($d -and $d.LogPixels) { [int]$d.LogPixels } "
        "else { 0 }"
    )
    try:
        completed = subprocess.run(
            [ps, "-NoProfile", "-NonInteractive", "-Command", script],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return None

    text = (completed.stdout or "").strip().splitlines()
    if not text:
        return None
    try:
        dpi = int(text[-1].strip())
    except ValueError:
        return None
    if dpi < 96:
        return None
    return _clamp_scale(dpi / 96.0)


def _windows_scale_via_ctypes() -> Optional[float]:
    try:
        import ctypes
        from ctypes import wintypes
    except Exception:
        return None

    try:
        # Prefer GetDpiForSystem (Win10+)
        get_dpi = ctypes.windll.user32.GetDpiForSystem
        get_dpi.restype = wintypes.UINT
        dpi = int(get_dpi())
        if dpi >= 96:
            return _clamp_scale(dpi / 96.0)
    except Exception:
        pass

    try:
        hdc = ctypes.windll.user32.GetDC(0)
        dpi = int(ctypes.windll.gdi32.GetDeviceCaps(hdc, 88))  # LOGPIXELSX
        ctypes.windll.user32.ReleaseDC(0, hdc)
        if dpi >= 96:
            return _clamp_scale(dpi / 96.0)
    except Exception:
        pass
    return None


def _find_powershell() -> Optional[str]:
    candidates = [
        "powershell.exe",
        "/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe",
        "pwsh.exe",
        "pwsh",
    ]
    for name in candidates:
        if name.startswith("/"):
            if os.path.isfile(name):
                return name
            continue
        from shutil import which

        found = which(name)
        if found:
            return found
    return None


def _enable_windows_dpi_awareness() -> None:
    try:
        import ctypes

        ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
        return
    except Exception:
        pass
    try:
        import ctypes

        ctypes.windll.shcore.SetProcessDpiAwareness(2)
        return
    except Exception:
        pass
    try:
        import ctypes

        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass


def screen_scale_factor(app: Optional[QApplication] = None) -> float:
    """Scale factor for *stylesheet* px lengths.

    When ``QT_SCALE_FACTOR`` is already active, return ``1.0`` so we do not
    double-scale style sheets. Otherwise use the screen DPR / logical DPI.
    """
    if _INJECTED_QT_SCALE is not None or os.environ.get("QT_SCALE_FACTOR"):
        # Global Qt scale already multiplies the UI.
        return 1.0

    application = app or QApplication.instance()
    screen = None
    if application is not None:
        screen = application.primaryScreen()
    if screen is None:
        screen = QGuiApplication.primaryScreen()
    if screen is None:
        return 1.0

    dpr = float(screen.devicePixelRatio())
    logical_dpi = float(screen.logicalDotsPerInch())
    dpi_scale = logical_dpi / 96.0 if logical_dpi > 0 else 1.0
    return _clamp_scale(max(dpr, dpi_scale, 1.0))


def effective_ui_scale(app: Optional[QApplication] = None) -> float:
    """Human-facing scale factor (for status / debug)."""
    if _INJECTED_QT_SCALE is not None:
        return _INJECTED_QT_SCALE
    env = _parse_positive_float(os.environ.get("QT_SCALE_FACTOR"))
    if env is not None:
        return env
    application = app or QApplication.instance()
    screen = application.primaryScreen() if application else None
    if screen is None:
        return 1.0
    return _clamp_scale(max(float(screen.devicePixelRatio()), 1.0))


def sp(value: float, scale: float) -> int:
    """Scale a design-pixel length for stylesheets / fixed metrics."""
    return max(1, int(round(value * scale)))


def scale_stylesheet(template: str, scale: float) -> str:
    """Replace ``Npx`` tokens in a stylesheet template with scaled values."""
    if abs(scale - 1.0) < 0.01:
        return template

    def repl(match: re.Match[str]) -> str:
        raw = float(match.group(1))
        return f"{sp(raw, scale)}px"

    return re.sub(r"(\d+(?:\.\d+)?)px", repl, template)


def _parse_positive_float(value: Optional[str]) -> Optional[float]:
    if value is None or str(value).strip() == "":
        return None
    try:
        number = float(str(value).strip())
    except ValueError:
        return None
    if number <= 0:
        return None
    return _clamp_scale(number)


def _clamp_scale(scale: float) -> float:
    return min(max(float(scale), 0.75), 4.0)


def _format_scale(scale: float) -> str:
    # Avoid long floats in the environment (1.2500001 → 1.25).
    text = f"{scale:.4f}".rstrip("0").rstrip(".")
    return text or "1"
