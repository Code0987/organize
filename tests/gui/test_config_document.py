"""Tests for GUI config models (no Qt required)."""

from pathlib import Path

from ui.models.config_document import ConfigDocument
from ui.models.pipeline_item import PipelineItem
from ui.models.rule_item import RuleItem
from ui.services.config_io import document_to_yaml, validate_with_organize
from ui.services.runner import run_document


def test_roundtrip_example_yaml():
    doc = ConfigDocument.new_with_example()
    raw = doc.to_config_dict()
    again = ConfigDocument.from_config_dict(raw)
    assert len(again.rules) == 1
    assert again.rules[0].name == "Find PDFs"
    assert again.rules[0].filters[0].name == "extension"


def test_validate_example():
    doc = ConfigDocument.new_with_example()
    ok, message = validate_with_organize(doc)
    assert ok, message


def test_pipeline_item_not_filter():
    item = PipelineItem.from_config_dict("filter", {"not extension": "jpg"})
    assert item.inverted is True
    assert item.name == "extension"
    assert item.primary_value == "jpg"
    assert item.to_config_dict() == {"not extension": "jpg"}


def test_run_document_dry_run(tmp_path: Path):
    # Create a small tree and a rule that echos matching files.
    (tmp_path / "a.pdf").write_text("x")
    (tmp_path / "b.txt").write_text("y")
    doc = ConfigDocument(
        rules=[
            RuleItem(
                name="echo pdfs",
                locations=[str(tmp_path)],
                filters=[
                    PipelineItem(
                        kind="filter",
                        name="extension",
                        primary_value="pdf",
                    )
                ],
                actions=[
                    PipelineItem(
                        kind="action",
                        name="echo",
                        primary_value="found {path.name}",
                    )
                ],
            )
        ]
    )
    output = run_document(doc, simulate=True, working_dir=tmp_path)
    text = "\n".join(e.message for e in output.entries)
    assert "a.pdf" in text or "found a.pdf" in text
    assert output.error_count == 0


def test_document_to_yaml_contains_rules():
    yaml_text = document_to_yaml(ConfigDocument.new_with_example())
    assert "rules:" in yaml_text
    assert "extension" in yaml_text
