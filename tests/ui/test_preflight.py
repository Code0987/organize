"""Location preflight should explain missing folders instead of staying silent."""

from pathlib import Path

from ui.models.location_preflight import LocationPreflight
from ui.models.preset_library import PresetLibrary
from ui.models.rule_factory import RuleFactory


def test_missing_folder_is_a_warning() -> None:
    checks = LocationPreflight().inspect_rules(
        [{"name": "Hello", "locations": "~/this-folder-does-not-exist-organize"}]
    )
    assert len(checks) == 1
    assert checks[0].exists is False
    assert checks[0].file_count == 0
    assert checks[0].level == "warn"
    assert "does not exist" in checks[0].message.lower()


def test_existing_folder_reports_file_count(tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_text("x", encoding="utf-8")
    check = LocationPreflight().inspect_path("Demo", str(tmp_path))
    assert check.exists is True
    assert check.file_count == 1
    assert check.level == "info"


def test_new_rule_defaults_to_home() -> None:
    rule = RuleFactory().new_rule()
    assert rule["locations"] == ["~"]
    checks = LocationPreflight().inspect_rules([rule])
    assert checks[0].exists is True


def test_blank_preset_location_exists() -> None:
    preset = PresetLibrary().default()
    assert "locations: ~" in preset.yaml
    checks = LocationPreflight().inspect_rules(
        [{"name": "Hello", "locations": "~"}]
    )
    assert checks[0].exists is True
