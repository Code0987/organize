"""Factories for new rules and discovery of existing config files."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from organize.find_config import list_configs


class RuleFactory:
    """Create default rule dicts and list configs from disk."""

    def new_rule(
        self,
        name: str = "New rule",
        locations: Optional[Iterable[str]] = None,
    ) -> Dict[str, Any]:
        """Return a valid starter rule the visual editor can load."""
        return {
            "name": name,
            "enabled": True,
            "targets": "files",
            "locations": list(locations or ["~"]),
            "subfolders": False,
            "filter_mode": "all",
            "filters": [{"extension": "pdf"}, "name"],
            "actions": [{"echo": "Found {path.name}"}],
        }

    def discovered_configs(self) -> List[Path]:
        """Unique config files from organize's default search locations."""
        seen = set()
        result: List[Path] = []
        for path in list_configs():
            resolved = path.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            result.append(path)
        return result
