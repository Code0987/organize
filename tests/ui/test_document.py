"""Config document and YAML helper tests (no Qt required)."""

from organize import Config

from ui.models.config_document import ConfigDocument
from ui.models.named_entry import NamedEntry
from ui.models.preset_library import PresetLibrary
from ui.models.rule_factory import RuleFactory
from ui.models.rule_summary import RuleSummary


def test_parse_and_emit_named_entries() -> None:
    assert NamedEntry.parse("extension") == NamedEntry("extension", None, False)
    assert NamedEntry.parse({"not extension": "pdf"}) == NamedEntry(
        "extension", "pdf", True
    )
    assert NamedEntry.parse({"move": {"dest": "~/Docs/"}}) == NamedEntry(
        "move", {"dest": "~/Docs/"}, False
    )
    assert NamedEntry(name="echo", value="hello").emit() == {"echo": "hello"}
    assert NamedEntry(name="empty", inverted=True).emit() == "not empty"


def test_compact_params_drops_defaults_and_empties() -> None:
    cleaned = NamedEntry.compact(
        {"dest": "~/A/", "on_conflict": "rename_new", "extra": ""},
        {"on_conflict": "rename_new"},
    )
    assert cleaned == {"dest": "~/A/"}


def test_blank_document_is_valid_organize_config() -> None:
    document = ConfigDocument.blank()
    config = document.validate()
    assert len(config.rules) >= 1


def test_presets_parse_as_organize_configs() -> None:
    for preset in PresetLibrary().all():
        config = Config.from_string(preset.yaml)
        assert config.rules, preset.id


def test_set_rules_roundtrip() -> None:
    document = ConfigDocument.blank()
    rule = RuleFactory().new_rule("PDFs", ["~/Downloads"])
    document.set_rules([rule])
    loaded = document.rules()
    assert loaded[0]["name"] == "PDFs"
    assert "extension" in str(loaded[0]["filters"])
    Config.from_string(document.text)


def test_summarize_rule() -> None:
    text = RuleSummary().summarize(
        {
            "locations": ["~/Downloads", "~/Desktop"],
            "filters": [{"extension": "pdf"}],
            "actions": [{"move": "~/Documents/PDF/"}],
        }
    )
    assert "Downloads" in text
    assert "extension" in text
    assert "move" in text
