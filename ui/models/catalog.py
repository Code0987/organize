"""Look up interactive-editor schemas for filters and actions."""

from __future__ import annotations

from typing import Dict, List, Tuple

from organize.registry import ACTIONS, FILTERS

from ui.models.action_specs import ACTION_SPECS
from ui.models.filter_specs import FILTER_SPECS
from ui.models.item_spec import ItemSpec


class Catalog:
    """Bridge between organize's registry and the visual editor forms."""

    def filter_spec(self, name: str) -> ItemSpec:
        """Return the editor schema for ``name``, or a generic fallback."""
        if name in FILTER_SPECS:
            return FILTER_SPECS[name]
        return ItemSpec(
            name=name,
            title=name.replace("_", " ").title(),
            summary="Custom or unknown filter.",
            can_invert=True,
        )

    def action_spec(self, name: str) -> ItemSpec:
        """Return the editor schema for ``name``, or a generic fallback."""
        if name in ACTION_SPECS:
            return ACTION_SPECS[name]
        return ItemSpec(
            name=name,
            title=name.replace("_", " ").title(),
            summary="Custom or unknown action.",
        )

    def filter_names(self) -> List[str]:
        """Names shown in the Add Filter combo box."""
        return sorted(FILTER_SPECS.keys())

    def action_names(self) -> List[str]:
        """Names shown in the Add Action combo box."""
        return sorted(ACTION_SPECS.keys())

    def filter_specs(self) -> Dict[str, ItemSpec]:
        """All known filter schemas."""
        return FILTER_SPECS

    def action_specs(self) -> Dict[str, ItemSpec]:
        """All known action schemas."""
        return ACTION_SPECS

    def missing_from_registry(self) -> Tuple[List[str], List[str]]:
        """Return registry names that have no UI schema yet."""
        missing_filters = [name for name in FILTERS if name not in FILTER_SPECS]
        missing_actions = [name for name in ACTIONS if name not in ACTION_SPECS]
        return missing_filters, missing_actions
