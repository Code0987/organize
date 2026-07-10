"""Tests for ConfigDocument."""

from __future__ import annotations

from pathlib import Path

from organize_gui.models.config_document import ConfigDocument
from organize_gui.models.rule_data import RuleData


class TestConfigDocument:
    def test_create_empty_has_starter_rule(self) -> None:
        doc = ConfigDocument.create_empty()
        assert len(doc.rules) == 1
        assert doc.dirty is True
        assert doc.source_path is None

    def test_from_yaml_dict(self) -> None:
        doc = ConfigDocument.from_yaml_dict(
            {
                "rules": [
                    {
                        "locations": "~/Desktop",
                        "actions": [{"echo": "hi"}],
                    }
                ]
            },
            source_path=Path("/tmp/config.yaml"),
        )
        assert len(doc.rules) == 1
        assert doc.source_path == Path("/tmp/config.yaml")
        assert doc.dirty is False

    def test_from_empty_and_none(self) -> None:
        assert ConfigDocument.from_yaml_dict(None).rules == []
        assert ConfigDocument.from_yaml_dict({"rules": None}).rules == []
        assert ConfigDocument.from_yaml_dict({}).rules == []

    def test_to_yaml_dict(self) -> None:
        doc = ConfigDocument(rules=[RuleData.create_default()])
        data = doc.to_yaml_dict()
        assert "rules" in data
        assert isinstance(data["rules"], list)
        assert len(data["rules"]) == 1

    def test_dirty_flags(self) -> None:
        doc = ConfigDocument(rules=[], dirty=False)
        doc.mark_dirty()
        assert doc.dirty is True
        doc.mark_clean()
        assert doc.dirty is False

    def test_display_title(self) -> None:
        doc = ConfigDocument(rules=[], source_path=None, dirty=True)
        assert "Untitled" in doc.display_title()
        assert "*" in doc.display_title()
        doc.source_path = Path("/tmp/my.yaml")
        doc.mark_clean()
        assert doc.display_title() == "my.yaml"
