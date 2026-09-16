"""Human-readable one-line summaries of a rule dict."""

from __future__ import annotations

from typing import Any, Dict, List

from ui.models.named_entry import NamedEntry


class RuleSummary:
    """Turn a rule mapping into a short tooltip / list subtitle."""

    def location_paths(self, location: Any) -> List[str]:
        """Extract path strings from a location string or mapping."""
        if isinstance(location, str):
            return [location]
        if isinstance(location, dict):
            path = location.get("path", "")
            if isinstance(path, list):
                return [str(item) for item in path]
            return [str(path)] if path else []
        return []

    def summarize(self, rule: Dict[str, Any]) -> str:
        """Return ``locations · filters → actions``."""
        locations = rule.get("locations") or []
        if isinstance(locations, str):
            loc_txt = locations
        elif isinstance(locations, list):
            paths: List[str] = []
            for location in locations:
                paths.extend(self.location_paths(location))
            loc_txt = ", ".join(paths[:3]) or "(no locations)"
            if len(paths) > 3:
                loc_txt += f" +{len(paths) - 3}"
        else:
            loc_txt = str(locations)

        filter_names: List[str] = []
        for item in rule.get("filters") or []:
            try:
                entry = NamedEntry.parse(item)
                filter_names.append(f"not {entry.name}" if entry.inverted else entry.name)
            except ValueError:
                filter_names.append("?")

        action_names: List[str] = []
        for item in rule.get("actions") or []:
            try:
                action_names.append(NamedEntry.parse(item).name)
            except ValueError:
                action_names.append("?")

        filt = ", ".join(filter_names) or "no filters"
        acts = ", ".join(action_names) or "no actions"
        return f"{loc_txt}  ·  {filt}  →  {acts}"
