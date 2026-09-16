"""Shared setup for UI tests. Qt-dependent modules skip themselves if PyQt6 is absent."""

from __future__ import annotations

import os

# Headless CI / servers have no display. Must be set before QApplication.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
