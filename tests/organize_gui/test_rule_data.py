"""Tests for RuleData model."""

from __future__ import annotations

from organize_gui.models.action_data import ActionData
from organize_gui.models.filter_data import FilterData
from organize_gui.models.location_data import LocationData
from organize_gui.models.rule_data import RuleData


class TestRuleData:
    def test_create_default(self) -> None:
        rule = RuleData.create_default()
        assert rule.name
        assert rule.enabled is True
        assert rule.locations
        assert rule.actions
        assert rule.targets == "files"

    def test_to_yaml_minimal(self) -> None:
        rule = RuleData(
            name="Test",
            locations=[LocationData(path=["~/Downloads"])],
            actions=[ActionData(name="echo", params={"msg": "hi"})],
        )
        data = rule.to_yaml_dict()
        assert data["name"] == "Test"
        assert data["locations"] == "~/Downloads"
        assert data["actions"] == [{"echo": "hi"}]
        assert "enabled" not in data  # default True omitted
        assert "subfolders" not in data

    def test_to_yaml_includes_non_defaults(self) -> None:
        rule = RuleData(
            name="X",
            enabled=False,
            targets="dirs",
            subfolders=True,
            filter_mode="any",
            tags={"a", "b"},
            locations=[LocationData(path=["~/x"])],
            filters=[FilterData(name="empty")],
            actions=[ActionData(name="delete")],
        )
        data = rule.to_yaml_dict()
        assert data["enabled"] is False
        assert data["targets"] == "dirs"
        assert data["subfolders"] is True
        assert data["filter_mode"] == "any"
        assert set(data["tags"]) == {"a", "b"}
        assert data["filters"] == ["empty"]

    def test_from_yaml_dict(self) -> None:
        raw = {
            "name": "Find PDFs",
            "locations": ["~/Downloads"],
            "subfolders": True,
            "filters": [{"extension": "pdf"}],
            "actions": [{"echo": "Found PDF!"}],
        }
        rule = RuleData.from_yaml_dict(raw)
        assert rule.name == "Find PDFs"
        assert rule.subfolders is True
        assert rule.filters[0].name == "extension"
        assert "pdf" in rule.filters[0].params["extensions"]
        assert rule.actions[0].params["msg"] == "Found PDF!"

    def test_round_trip(self) -> None:
        rule = RuleData.create_default()
        rule.name = "Round trip"
        rule.filters = [
            FilterData(name="extension", params={"extensions": ["pdf"]}),
        ]
        rule.actions = [
            ActionData(name="echo", params={"msg": "x"}),
            ActionData(name="move", params={"dest": "~/out/", "on_conflict": "rename_new",
                                            "rename_template": "{name} {counter}{extension}",
                                            "autodetect_folder": True}),
        ]
        data = rule.to_yaml_dict()
        again = RuleData.from_yaml_dict(data)
        assert again.name == "Round trip"
        assert again.filters[0].name == "extension"
        assert again.actions[0].name == "echo"
        assert again.actions[1].name == "move"

    def test_display_label_disabled(self) -> None:
        rule = RuleData(name="N", enabled=False)
        assert "[disabled]" in rule.display_label()
