"""Integration tests: UI config models ↔ YAML ↔ organize engine."""

from __future__ import annotations

from pathlib import Path

import yaml

from organize import Config
from ui.models.config_document import ConfigDocument
from ui.models.pipeline_item import PipelineItem
from ui.models.rule_item import RuleItem
from ui.services.config_io import (
    ConfigIOError,
    document_to_yaml,
    load_config,
    save_config,
    validate_with_organize,
)
from ui.services.runner import run_document


def _pdf_echo_doc(root: Path) -> ConfigDocument:
    return ConfigDocument(
        rules=[
            RuleItem(
                name="Echo PDFs",
                enabled=True,
                locations=[str(root / "Downloads")],
                subfolders=False,
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
                        primary_value="PDF:{path.name}",
                    )
                ],
            )
        ]
    )


def test_ui_document_validates_and_parses_with_organize_engine(sample_tree: Path):
    doc = _pdf_echo_doc(sample_tree)
    ok, message = validate_with_organize(doc)
    assert ok, message

    yaml_text = document_to_yaml(doc)
    # organize's own parser must accept the GUI output
    cfg = Config.from_string(yaml_text)
    assert len(cfg.rules) == 1
    assert cfg.rules[0].name == "Echo PDFs"


def test_save_load_roundtrip_preserves_rules(tmp_path: Path, sample_tree: Path):
    doc = _pdf_echo_doc(sample_tree)
    path = tmp_path / "config.yaml"
    save_config(doc, path)
    assert path.is_file()

    loaded = load_config(path)
    assert loaded.path == path
    assert loaded.dirty is False
    assert len(loaded.rules) == 1
    rule = loaded.rules[0]
    assert rule.name == "Echo PDFs"
    assert rule.filters[0].name == "extension"
    assert rule.actions[0].name == "echo"
    assert str(sample_tree / "Downloads") in rule.locations


def test_load_invalid_yaml_raises(tmp_path: Path):
    bad = tmp_path / "bad.yaml"
    bad.write_text("rules: [\n  - this is: [unterminated", encoding="utf-8")
    try:
        load_config(bad)
        assert False, "expected ConfigIOError"
    except ConfigIOError as exc:
        assert "YAML" in str(exc) or "parse" in str(exc).lower() or "Invalid" in str(exc)


def test_dry_run_echo_matches_pdf_only(sample_tree: Path):
    doc = _pdf_echo_doc(sample_tree)
    output = run_document(doc, simulate=True, working_dir=sample_tree)
    messages = "\n".join(e.message for e in output.entries)
    assert "invoice.pdf" in messages
    assert "PDF:invoice.pdf" in messages or "invoice.pdf" in messages
    # txt / jpg should not be echoed by the PDF rule
    assert "notes.txt" not in messages
    assert output.error_count == 0
    # dry-run must not modify files
    assert (sample_tree / "Downloads" / "invoice.pdf").exists()
    assert (sample_tree / "Downloads" / "notes.txt").exists()


def test_dry_run_move_does_not_relocate_files(sample_tree: Path):
    dest = sample_tree / "Documents" / "PDFs"
    doc = ConfigDocument(
        rules=[
            RuleItem(
                name="Move PDFs",
                locations=[str(sample_tree / "Downloads")],
                filters=[
                    PipelineItem(kind="filter", name="extension", primary_value="pdf")
                ],
                actions=[
                    PipelineItem(
                        kind="action",
                        name="move",
                        primary_value=str(dest) + "/",
                    )
                ],
            )
        ]
    )
    ok, message = validate_with_organize(doc)
    assert ok, message

    output = run_document(doc, simulate=True, working_dir=sample_tree)
    assert output.error_count == 0
    # File still in Downloads after simulation
    assert (sample_tree / "Downloads" / "invoice.pdf").exists()
    assert not (dest / "invoice.pdf").exists()


def test_live_run_move_relocates_file(sample_tree: Path):
    dest_dir = sample_tree / "Documents" / "PDFs"
    doc = ConfigDocument(
        rules=[
            RuleItem(
                name="Move PDFs live",
                locations=[str(sample_tree / "Downloads")],
                filters=[
                    PipelineItem(kind="filter", name="extension", primary_value="pdf")
                ],
                actions=[
                    PipelineItem(
                        kind="action",
                        name="move",
                        params={
                            "dest": str(dest_dir) + "/",
                            "on_conflict": "overwrite",
                        },
                    )
                ],
            )
        ]
    )
    output = run_document(doc, simulate=False, working_dir=sample_tree)
    assert output.error_count == 0
    assert not (sample_tree / "Downloads" / "invoice.pdf").exists()
    assert (dest_dir / "invoice.pdf").exists()
    # Non-PDF untouched
    assert (sample_tree / "Downloads" / "notes.txt").exists()


def test_multi_rule_filter_mode_and_tags_roundtrip(tmp_path: Path):
    doc = ConfigDocument(
        rules=[
            RuleItem(
                name="Tagged",
                tags=["nightly", "docs"],
                filter_mode="any",
                targets="files",
                locations=["~/Downloads"],
                filters=[
                    PipelineItem(kind="filter", name="extension", primary_value="pdf"),
                    PipelineItem(
                        kind="filter",
                        name="name",
                        params={"contains": ["Invoice"], "case_sensitive": False},
                    ),
                ],
                actions=[
                    PipelineItem(kind="action", name="echo", primary_value="{path}")
                ],
            ),
            RuleItem(
                name="Disabled dirs",
                enabled=False,
                targets="dirs",
                locations=["/tmp"],
                filters=[PipelineItem(kind="filter", name="empty")],
                actions=[PipelineItem(kind="action", name="trash")],
            ),
        ]
    )
    path = tmp_path / "multi.yaml"
    save_config(doc, path)
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert raw["rules"][0]["filter_mode"] == "any"
    assert set(raw["rules"][0]["tags"]) == {"nightly", "docs"}
    assert raw["rules"][1]["enabled"] is False
    assert raw["rules"][1]["targets"] == "dirs"

    loaded = load_config(path)
    assert loaded.rules[0].filter_mode == "any"
    assert set(loaded.rules[0].tags) == {"nightly", "docs"}
    assert loaded.rules[1].enabled is False
    ok, message = validate_with_organize(loaded)
    assert ok, message


def test_inverted_filter_emitted_for_organize(sample_tree: Path):
    doc = ConfigDocument(
        rules=[
            RuleItem(
                name="Non-pdfs",
                locations=[str(sample_tree / "Downloads")],
                filters=[
                    PipelineItem(
                        kind="filter",
                        name="extension",
                        primary_value="pdf",
                        inverted=True,
                    )
                ],
                actions=[
                    PipelineItem(
                        kind="action",
                        name="echo",
                        primary_value="other:{path.name}",
                    )
                ],
            )
        ]
    )
    yaml_text = document_to_yaml(doc)
    assert "not extension" in yaml_text
    output = run_document(doc, simulate=True, working_dir=sample_tree)
    text = "\n".join(e.message for e in output.entries)
    assert "notes.txt" in text
    assert "photo.JPG" in text or "photo.jpg" in text.lower()
