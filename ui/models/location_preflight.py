"""Check rule locations before a run so missing folders are not silent."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List


@dataclass(frozen=True)
class LocationCheck:
    """Result of inspecting one rule location."""

    rule_name: str
    raw: str
    resolved: Path
    exists: bool
    is_dir: bool
    file_count: int
    message: str
    level: str  # "info" | "warn"


class LocationPreflight:
    """Expand ``~`` / env vars and report missing or empty search folders.

    organize itself treats a missing location as "zero files" and prints
    *Nothing to do*. The GUI uses this check so dry-run explains why.
    """

    def inspect_rules(self, rules: Iterable[Dict[str, Any]]) -> List[LocationCheck]:
        """Return one :class:`LocationCheck` per location on each rule."""
        results: List[LocationCheck] = []
        for rule in rules:
            name = str(rule.get("name") or "Untitled rule")
            subfolders = bool(rule.get("subfolders", False))
            for raw in self.location_strings(rule.get("locations")):
                results.append(self.inspect_path(name, raw, subfolders=subfolders))
        return results

    def location_strings(self, locations: Any) -> List[str]:
        """Flatten a rule's ``locations`` value into path strings."""
        if locations is None:
            return []
        if isinstance(locations, str):
            return [locations]
        if not isinstance(locations, list):
            return []
        paths: List[str] = []
        for item in locations:
            if isinstance(item, str):
                paths.append(item)
            elif isinstance(item, dict):
                path = item.get("path", "")
                if isinstance(path, list):
                    paths.extend(str(part) for part in path if part)
                elif path:
                    paths.append(str(path))
        return paths

    def inspect_path(
        self,
        rule_name: str,
        raw: str,
        *,
        subfolders: bool = False,
    ) -> LocationCheck:
        """Resolve ``raw`` and describe whether organize will see files there."""
        resolved = Path(os.path.expandvars(os.path.expanduser(raw)))
        if not resolved.exists():
            return LocationCheck(
                rule_name=rule_name,
                raw=raw,
                resolved=resolved,
                exists=False,
                is_dir=False,
                file_count=0,
                level="warn",
                message=(
                    f"Location does not exist: {resolved} "
                    f"(from {raw!r}). organize will find 0 files here. "
                    "Use Add folder to pick a folder that exists."
                ),
            )
        if not resolved.is_dir():
            return LocationCheck(
                rule_name=rule_name,
                raw=raw,
                resolved=resolved,
                exists=True,
                is_dir=False,
                file_count=0,
                level="warn",
                message=f"Location is not a folder: {resolved}",
            )
        count = self._count_files(resolved, subfolders=subfolders)
        if count == 0:
            depth = "including subfolders" if subfolders else "top level only"
            return LocationCheck(
                rule_name=rule_name,
                raw=raw,
                resolved=resolved,
                exists=True,
                is_dir=True,
                file_count=0,
                level="warn",
                message=(
                    f"No files in {resolved} ({depth}). "
                    "Enable Include subfolders or choose another folder."
                ),
            )
        return LocationCheck(
            rule_name=rule_name,
            raw=raw,
            resolved=resolved,
            exists=True,
            is_dir=True,
            file_count=count,
            level="info",
            message=f"Found {count} file(s) in {resolved}",
        )

    def _count_files(self, root: Path, *, subfolders: bool) -> int:
        try:
            if subfolders:
                return sum(1 for path in root.rglob("*") if path.is_file())
            return sum(1 for path in root.iterdir() if path.is_file())
        except OSError:
            return 0

    def resolve(self, raw: str) -> Path:
        """Expand ``~`` and environment variables in a location string."""
        return Path(os.path.expandvars(os.path.expanduser(raw)))
