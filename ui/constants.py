"""Shared constants for the organize desktop UI."""

from __future__ import annotations

from typing import Tuple

# Documentation and application identity.
DOCS_URL: str = "https://organize.readthedocs.io"
APP_NAME: str = "organize"
ORG_NAME: str = "organize"
SETTINGS_KEY_LAST_CONFIG: str = "last_config"

# Conflict-resolution options accepted by move/copy/rename/link actions.
CONFLICT_MODES: Tuple[str, ...] = (
    "rename_new",
    "rename_existing",
    "skip",
    "overwrite",
    "trash",
    "deduplicate",
)

# Dark theme palette.
ACCENT: str = "#38bdf8"
ACCENT_HOVER: str = "#7dd3fc"
SUCCESS: str = "#34d399"
WARNING: str = "#fbbf24"
DANGER: str = "#f87171"
BG: str = "#0b1220"
SURFACE: str = "#111827"
ELEVATED: str = "#1f2937"
BORDER: str = "#334155"
TEXT: str = "#e5e7eb"
MUTED: str = "#94a3b8"
