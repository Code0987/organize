from __future__ import annotations

import pytest

from organize_gui.models.filter_data import FilterData


class TestFilterDataRoundTrip:
    def test_extension_shorthand_string(self) -> None:
        filt = FilterData.from_yaml_value({"extension": "pdf"})
        assert filt.name == "extension"
        assert "pdf" in filt.params["extensions"]
        out = filt.to_yaml_value()
        assert out == {"extension": ["pdf"]} or out == {"extension": "pdf"} or (
            isinstance(out, dict) and "extension" in out
        )

    def test_extension_list(self) -> None:
        filt = FilterData.from_yaml_value({"extension": ["pdf", "jpg"]})
        assert set(filt.params["extensions"]) == {"pdf", "jpg"}

    def test_name_with_options(self) -> None:
        filt = FilterData.from_yaml_value(
            {
                "name": {
                    "contains": ["Invoice", "Order"],
                    "case_sensitive": False,
                }
            }
        )
        assert filt.name == "name"
        assert filt.params["contains"] == ["Invoice", "Order"]
        assert filt.params["case_sensitive"] is False
        out = filt.to_yaml_value()
        assert isinstance(out, dict)
        assert "name" in out
        body = out["name"]
        assert body["contains"] == ["Invoice", "Order"]
        assert body["case_sensitive"] is False

    def test_inverted_filter(self) -> None:
        filt = FilterData.from_yaml_value({"not extension": "tmp"})
        assert filt.name == "extension"
        assert filt.inverted is True
        out = filt.to_yaml_value()
        assert isinstance(out, dict)
        assert "not extension" in out

    def test_empty_filter_string(self) -> None:
        filt = FilterData.from_yaml_value("empty")
        assert filt.name == "empty"
        assert filt.to_yaml_value() == "empty"

    def test_not_empty_string(self) -> None:
        filt = FilterData.from_yaml_value("not empty")
        assert filt.name == "empty"
        assert filt.inverted is True
        assert filt.to_yaml_value() == "not empty"

    def test_regex_primary(self) -> None:
        filt = FilterData.from_yaml_value({"regex": r"(?P<id>\d+)"})
        assert filt.name == "regex"
        assert filt.params["expr"] == r"(?P<id>\d+)"
        out = filt.to_yaml_value()
        assert out == {"regex": r"(?P<id>\d+)"}

    def test_size_conditions(self) -> None:
        filt = FilterData.from_yaml_value({"size": ">= 500 MB"})
        assert filt.name == "size"
        assert filt.params["conditions"] == [">= 500 MB"] or (
            ">= 500 MB" in filt.params.get("conditions", [])
        )

    def test_create_default(self) -> None:
        filt = FilterData.create_default("extension")
        assert filt.name == "extension"
        assert "extensions" in filt.params

    def test_display_label_includes_summary(self) -> None:
        filt = FilterData(
            name="extension",
            params={"extensions": ["pdf", "docx"]},
        )
        label = filt.display_label()
        assert "pdf" in label
