"""Catalog coverage against organize's live filter/action registry."""

from organize.registry import ACTIONS, FILTERS

from ui.models.action_specs import ACTION_SPECS
from ui.models.catalog import Catalog
from ui.models.filter_specs import FILTER_SPECS


def test_catalog_covers_every_registered_filter_and_action() -> None:
    missing_filters, missing_actions = Catalog().missing_from_registry()
    assert missing_filters == []
    assert missing_actions == []


def test_specs_exist_for_known_names() -> None:
    catalog = Catalog()
    assert catalog.filter_spec("extension").title == "Extension"
    assert catalog.action_spec("move").fields[0].key == "dest"
    assert set(FILTER_SPECS) == set(FILTERS)
    assert set(ACTION_SPECS) == set(ACTIONS)
