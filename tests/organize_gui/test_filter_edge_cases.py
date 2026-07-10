"""Edge-case tests for filter YAML parsing (including known footguns)."""

from __future__ import annotations

import pytest

from organize_gui.models.filter_data import FilterData
from organize_gui.services.config_service import ConfigService
from organize_gui.models.config_document import ConfigDocument
from organize_gui.models.rule_data import RuleData
from organize_gui.models.location_data import LocationData
from organize_gui.models.action_data import ActionData


class TestSizeFilterParsing:
    def test_size_condition_string_kept_intact(self) -> None:
        """Size shorthand '>= 500 MB' must remain a single condition string.

        Splitting on whitespace would produce invalid size tokens.
        """
        filt = FilterData.from_yaml_value({"size": ">= 500 MB"})
        assert filt.params["conditions"] == [">= 500 MB"]

    def test_size_compound_condition(self) -> None:
        filt = FilterData.from_yaml_value({"size": ">20k, < 1 TB"})
        # Either one compound string or two conditions — must validate with organize
        conditions = filt.params["conditions"]
        assert conditions
        # Rebuild a config and validate
        doc = ConfigDocument(
            rules=[
                RuleData(
                    locations=[LocationData(path=["~/Downloads"])],
                    filters=[filt],
                    actions=[ActionData(name="echo", params={"msg": "x"})],
                )
            ]
        )
        ok, msg = ConfigService.validate(doc)
        assert ok, msg


class TestInvertedAndUnknown:
    def test_unknown_filter_round_trips_name(self) -> None:
        filt = FilterData.from_yaml_value({"custom_filter": {"foo": 1}})
        assert filt.name == "custom_filter"
        out = filt.to_yaml_value()
        assert isinstance(out, dict)
        assert "custom_filter" in out
