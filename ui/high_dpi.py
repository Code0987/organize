"""HiDPI / Windows display-scale detection for the PyQt6 GUI.

The app often runs under WSL or an X/Wayland forwarder. Those stacks
report 96 DPI even when Windows is at 125% or 150%. Qt then paints a
tiny 1× UI that the compositor stretches — small and blurry.

This module must run *before* ``QApplication`` is created.
"""

from __future__ import annotations

import os
import re
import subprocess
from typing import Optional


class HighDpi:
    """Detect the host scale factor and export Qt environment variables."""

    def apply(self) -> float:
        """Set Qt scale env vars. Return the factor that will be used."""
        if os.environ.get("QT_QPA_PLATFORM", "").lower() == "offscreen":
            return 1.0
        if os.environ.get("QT_SCALE_FACTOR"):
            try:
                return float(os.environ["QT_SCALE_FACTOR"])
            except ValueError:
                return 1.0

        os.environ.setdefault("QT_ENABLE_HIGHDPI_SCALING", "1")
        os.environ.setdefault("QT_AUTO_SCREEN_SCALE_FACTOR", "1")
        os.environ.setdefault("QT_SCALE_FACTOR_ROUNDING_POLICY", "PassThrough")

        scale = self.detect_scale()
        if scale > 1.01:
            # Force Qt to paint at the Windows scale instead of 1×-then-stretch.
            os.environ["QT_SCALE_FACTOR"] = f"{scale:.2f}"
        return scale

    def detect_scale(self) -> float:
        """Return a snapped scale such as 1.0, 1.25, 1.5, or 2.0."""
        pixels = self._windows_log_pixels()
        if pixels is None:
            return 1.0
        return self.snap(pixels / 96.0)

    @staticmethod
    def snap(scale: float) -> float:
        """Snap to the scale steps Windows actually uses."""
        if scale <= 0:
            return 1.0
        steps = (1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 3.0)
        return min(steps, key=lambda step: abs(step - scale))

    def _windows_log_pixels(self) -> Optional[int]:
        """Read the Windows log-pixels value (96 = 100%, 120 = 125%, …)."""
        for reader in (self._from_reg, self._from_powershell):
            value = reader()
            if value is not None:
                return value
        return None

    def _from_reg(self) -> Optional[int]:
        reg = self._reg_exe()
        if reg is None:
            return None
        queries = (
            (r"HKCU\Control Panel\Desktop", "LogPixels"),
            (r"HKCU\Control Panel\Desktop\WindowMetrics", "AppliedDPI"),
        )
        for key, value_name in queries:
            parsed = self._query_reg(reg, key, value_name)
            if parsed is not None:
                return parsed
        return None

    def _query_reg(self, reg: str, key: str, value_name: str) -> Optional[int]:
        try:
            completed = subprocess.run(
                [reg, "query", key, "/v", value_name],
                check=False,
                capture_output=True,
                text=True,
                timeout=3,
            )
        except (OSError, subprocess.TimeoutExpired):
            return None
        if completed.returncode != 0:
            return None
        return self.parse_reg_dword(completed.stdout)

    @staticmethod
    def parse_reg_dword(output: str) -> Optional[int]:
        """Parse ``REG_DWORD`` hex from ``reg.exe query`` output."""
        match = re.search(r"REG_DWORD\s+0x([0-9a-fA-F]+)", output)
        if not match:
            return None
        value = int(match.group(1), 16)
        if value < 72 or value > 480:
            return None
        return value

    def _from_powershell(self) -> Optional[int]:
        for command in (
            "(Get-ItemProperty 'HKCU:\\Control Panel\\Desktop').LogPixels",
            "(Get-ItemProperty 'HKCU:\\Control Panel\\Desktop\\WindowMetrics').AppliedDPI",
        ):
            try:
                completed = subprocess.run(
                    ["powershell.exe", "-NoProfile", "-Command", command],
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
            except (OSError, subprocess.TimeoutExpired):
                continue
            if completed.returncode != 0:
                continue
            text = (completed.stdout or "").strip().splitlines()
            if not text:
                continue
            try:
                value = int(text[-1].strip())
            except ValueError:
                continue
            if 72 <= value <= 480:
                return value
        return None

    @staticmethod
    def _reg_exe() -> Optional[str]:
        candidates = (
            "reg.exe",
            "/mnt/c/Windows/System32/reg.exe",
            "C:\\Windows\\System32\\reg.exe",
        )
        for path in candidates:
            if os.path.sep in path and not os.path.exists(path):
                continue
            return path
        return None
