"""YAML load/dump helpers for organize config documents."""

from __future__ import annotations

from typing import Any

import yaml


class YamlCodec:
    """Thin wrapper around PyYAML with organize-friendly defaults."""

    def loads(self, text: str) -> Any:
        """Parse YAML text. Empty documents become an empty mapping."""
        return yaml.safe_load(text) or {}

    def dumps(self, data: Any) -> str:
        """Serialize ``data`` without sorting keys so rule order is kept."""
        return yaml.safe_dump(
            data,
            sort_keys=False,
            allow_unicode=True,
            default_flow_style=False,
        )
