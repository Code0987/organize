"""Detect and watch the operating system light/dark preference."""

from __future__ import annotations

import os
import subprocess
import sys
from shutil import which
from typing import Optional

from PyQt6.QtCore import QObject, QTimer, pyqtSignal
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

from ui.styles.palette import ThemeMode


def detect_system_theme() -> ThemeMode:
    """Return the preferred theme from system settings.

    Resolution order:
    1. ``ORGANIZE_THEME`` env (``light`` / ``dark`` / ``system``)
    2. Qt ``styleHints().colorScheme()`` when known
    3. Windows ``AppsUseLightTheme`` registry value (works from WSL)
    4. GNOME ``gsettings`` color-scheme / gtk-theme
    5. Default: light
    """
    forced = (os.environ.get("ORGANIZE_THEME") or "").strip().lower()
    if forced in {"light", "dark"}:
        return ThemeMode(forced)

    if os.environ.get("ORGANIZE_SKIP_HOST_PROBES") == "1":
        # Tests / constrained environments: do not shell out for theme detection.
        return ThemeMode.LIGHT

    # Qt 6.5+ color scheme (may be Unknown under WSLg).
    app = QApplication.instance() or QGuiApplication.instance()
    if app is not None:
        try:
            scheme = app.styleHints().colorScheme()
            if scheme == Qt.ColorScheme.Dark:
                return ThemeMode.DARK
            if scheme == Qt.ColorScheme.Light:
                return ThemeMode.LIGHT
        except Exception:
            pass

    windows = _windows_apps_use_light_theme()
    if windows is False:
        return ThemeMode.DARK
    if windows is True:
        return ThemeMode.LIGHT

    gnome = _gnome_prefers_dark()
    if gnome is True:
        return ThemeMode.DARK
    if gnome is False:
        return ThemeMode.LIGHT

    # macOS via defaults (best-effort when running natively).
    if sys.platform == "darwin":
        mac = _macos_prefers_dark()
        if mac is True:
            return ThemeMode.DARK
        if mac is False:
            return ThemeMode.LIGHT

    return ThemeMode.LIGHT


def _windows_apps_use_light_theme() -> Optional[bool]:
    """Return True if Windows apps prefer light, False for dark, else None."""
    if sys.platform == "win32":
        try:
            import winreg

            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
            )
            value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
            winreg.CloseKey(key)
            return bool(int(value))
        except Exception:
            pass

    ps = _find_powershell()
    if ps is None:
        return None
    script = (
        "$p = Get-ItemProperty -Path "
        "'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize' "
        "-ErrorAction SilentlyContinue; "
        "if ($null -eq $p -or $null -eq $p.AppsUseLightTheme) { 'unknown' } "
        "else { [string]$p.AppsUseLightTheme }"
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
    token = text[-1].strip().lower()
    if token in {"0", "false"}:
        return False
    if token in {"1", "true"}:
        return True
    return None


def _gnome_prefers_dark() -> Optional[bool]:
    gsettings = which("gsettings")
    if not gsettings:
        return None
    try:
        completed = subprocess.run(
            [gsettings, "get", "org.gnome.desktop.interface", "color-scheme"],
            check=False,
            capture_output=True,
            text=True,
            timeout=2,
        )
        value = (completed.stdout or "").lower()
        if "prefer-dark" in value:
            return True
        if "prefer-light" in value or "default" in value:
            # "default" is ambiguous; fall through to gtk-theme.
            if "prefer-light" in value:
                return False
    except (OSError, subprocess.SubprocessError):
        return None

    try:
        completed = subprocess.run(
            [gsettings, "get", "org.gnome.desktop.interface", "gtk-theme"],
            check=False,
            capture_output=True,
            text=True,
            timeout=2,
        )
        value = (completed.stdout or "").lower()
        if "dark" in value:
            return True
        if value.strip():
            return False
    except (OSError, subprocess.SubprocessError):
        return None
    return None


def _macos_prefers_dark() -> Optional[bool]:
    try:
        completed = subprocess.run(
            ["defaults", "read", "-g", "AppleInterfaceStyle"],
            check=False,
            capture_output=True,
            text=True,
            timeout=2,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if completed.returncode != 0:
        # Key missing usually means light mode.
        return False
    return "dark" in (completed.stdout or "").lower()


def _find_powershell() -> Optional[str]:
    candidates = [
        "powershell.exe",
        "/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe",
        "pwsh.exe",
        "pwsh",
    ]
    for name in candidates:
        if name.startswith("/") and os.path.isfile(name):
            return name
        found = which(name)
        if found:
            return found
    return None


class ThemeWatcher(QObject):
    """Emits :attr:`theme_changed` when the system appearance changes."""

    theme_changed = pyqtSignal(object)  # ThemeMode

    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._current = detect_system_theme()

        app = QApplication.instance()
        if app is not None:
            try:
                app.styleHints().colorSchemeChanged.connect(self._on_qt_scheme_changed)
            except Exception:
                pass

        # WSLg often reports Qt ColorScheme.Unknown and never emits changes.
        # Poll the Windows registry / gsettings as a reliable fallback.
        self._timer = QTimer(self)
        self._timer.setInterval(2000)
        self._timer.timeout.connect(self._poll)
        self._timer.start()

    @property
    def current(self) -> ThemeMode:
        """Last known system theme."""
        return self._current

    def _on_qt_scheme_changed(self, scheme: object) -> None:
        self._recompute()

    def _poll(self) -> None:
        self._recompute()

    def _recompute(self) -> None:
        detected = detect_system_theme()
        if detected is not self._current:
            self._current = detected
            self.theme_changed.emit(detected)
