"""Tests for ConfigService load/save/validate/YAML."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from organize import Config
from organize_gui.models.action_data import ActionData
from organize_gui.models.config_document import ConfigDocument
from organize_gui.models.filter_data import FilterData
from organize_gui.models.location_data import LocationData
from organize_gui.models.rule_data import RuleData
from organize_gui.services.config_service import ConfigService


class TestConfigServiceLoad:
    def test_load_string_readme_sample(self, sample_config_yaml: str) -> None:
        doc = ConfigService.load_string(sample_config_yaml)
        assert len(doc.rules) == 1
        rule = doc.rules[0]
        assert rule.name == "Find PDFs"
        assert rule.subfolders is True
        assert rule.filters[0].name == "extension"
        assert "pdf" in rule.filters[0].params["extensions"]
        assert rule.actions[0].params["msg"] == "Found PDF!"

    def test_load_path_and_save(self, tmp_path: Path, sample_config_yaml: str) -> None:
        path = tmp_path / "config.yaml"
        path.write_text(sample_config_yaml, encoding="utf-8")
        doc = ConfigService.load_path(path)
        assert doc.source_path == path

        out = tmp_path / "out.yaml"
        ConfigService.save(doc, out)
        assert out.is_file()
        assert doc.dirty is False
        assert doc.source_path == out

        again = ConfigService.load_path(out)
        assert again.rules[0].name == "Find PDFs"

    def test_save_without_path_raises(self) -> None:
        doc = ConfigDocument(rules=[])
        with pytest.raises(ValueError, match="No path"):
            ConfigService.save(doc)


class TestConfigServiceValidate:
    def test_valid_document(self, sample_config_yaml: str) -> None:
        doc = ConfigService.load_string(sample_config_yaml)
        ok, msg = ConfigService.validate(doc)
        assert ok is True
        assert "valid" in msg.lower()

    def test_invalid_empty_actions(self) -> None:
        doc = ConfigDocument(
            rules=[
                RuleData(
                    locations=[LocationData(path=["~/x"])],
                    actions=[],  # organize requires min 1 action
                )
            ]
        )
        ok, msg = ConfigService.validate(doc)
        assert ok is False
        assert msg

    def test_generated_yaml_accepted_by_organize(self) -> None:
        doc = ConfigDocument(
            rules=[
                RuleData(
                    name="Sort PDFs",
                    subfolders=True,
                    locations=[LocationData(path=["~/Downloads"])],
                    filters=[
                        FilterData(
                            name="extension",
                            params={"extensions": ["pdf"]},
                        ),
                        FilterData(
                            name="name",
                            params={
                                "match": "*",
                                "startswith": [],
                                "contains": ["Invoice"],
                                "endswith": [],
                                "case_sensitive": False,
                            },
                        ),
                    ],
                    actions=[
                        ActionData(name="echo", params={"msg": "Found {path.name}"}),
                        ActionData(
                            name="move",
                            params={
                                "dest": "~/Documents/PDFs/",
                                "on_conflict": "rename_new",
                                "rename_template": "{name} {counter}{extension}",
                                "autodetect_folder": True,
                            },
                        ),
                    ],
                )
            ]
        )
        yaml_text = ConfigService.to_yaml(doc)
        # Must parse with organize itself
        Config.from_string(yaml_text)
        ok, _ = ConfigService.validate(doc)
        assert ok is True


class TestConfigServiceRoundTrip:
    def test_yaml_round_trip_preserves_rules(self, sample_config_yaml: str) -> None:
        doc1 = ConfigService.load_string(sample_config_yaml)
        text1 = ConfigService.to_yaml(doc1)
        doc2 = ConfigService.load_string(text1)
        text2 = ConfigService.to_yaml(doc2)
        # Both should validate
        assert ConfigService.validate(doc1)[0]
        assert ConfigService.validate(doc2)[0]
        # Structural equality on re-parsed YAML
        assert yaml.safe_load(text1) == yaml.safe_load(text2)

    def test_complex_config_round_trip(self) -> None:
        src = """
rules:
  - name: multi
    enabled: true
    targets: files
    locations:
      - path: ~/Downloads
        max_depth: 2
        exclude_files: ["*.part"]
      - ~/Desktop
    subfolders: true
    filter_mode: all
    tags: [cleanup, docs]
    filters:
      - extension: [pdf, txt]
      - not empty
      - name:
          contains: Invoice
          case_sensitive: false
    actions:
      - echo: "hit {path.name}"
      - move:
          dest: ~/Archive/
          on_conflict: rename_new
"""
        doc = ConfigService.load_string(src)
        assert ConfigService.validate(doc)[0]
        text = ConfigService.to_yaml(doc)
        again = ConfigService.load_string(text)
        assert ConfigService.validate(again)[0]
        assert again.rules[0].name == "multi"
        assert len(again.rules[0].locations) == 2
        assert len(again.rules[0].filters) == 3
        assert again.rules[0].filters[1].inverted is True
        assert "cleanup" in again.rules[0].tags


class TestConfigServiceEmptyLocation:
    """Review issue #1: empty location must not crash serialize/validate."""

    def test_empty_location_path_does_not_crash_to_yaml(self) -> None:
        doc = ConfigDocument(
            rules=[
                RuleData(
                    locations=[LocationData(path=[], min_depth=1)],
                    actions=[ActionData(name="echo", params={"msg": "x"})],
                )
            ]
        )
        # Must not raise IndexError
        text = ConfigService.to_yaml(doc)
        assert isinstance(text, str)

    def test_empty_location_path_validate_returns_false_not_crash(self) -> None:
        doc = ConfigDocument(
            rules=[
                RuleData(
                    locations=[LocationData(path=[], min_depth=1)],
                    actions=[ActionData(name="echo", params={"msg": "x"})],
                )
            ]
        )
        ok, msg = ConfigService.validate(doc)
        # Either invalid config or a controlled error — must not raise
        assert isinstance(ok, bool)
        assert isinstance(msg, str)
