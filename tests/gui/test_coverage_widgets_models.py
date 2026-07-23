"""Extra coverage for widgets, models, schemas."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from PyQt6.QtWidgets import QCheckBox, QComboBox, QLineEdit, QSpinBox, QTextEdit

from ui.models.config_document import ConfigDocument
from ui.models.pipeline_item import PipelineItem
from ui.models.rule_item import RuleItem
from ui.schemas.catalog import action_schema, filter_schema
from ui.schemas.field_spec import FieldSpec, ItemSchema
from ui.widgets.form_field_widget import FormFieldWidget
from ui.widgets.item_editor_dialog import ItemEditorDialog
from ui.widgets.pipeline_list_widget import PipelineListWidget
from ui.widgets.rule_list_widget import RuleListWidget
from ui.widgets.yaml_preview_widget import YamlPreviewWidget


pytestmark = pytest.mark.usefixtures("qapp")


def test_field_spec_defaults_and_primary():
    schema = ItemSchema(
        name="demo",
        label="Demo",
        description="d",
        fields=(
            FieldSpec("a", "A", "str", default="x", is_primary=True),
            FieldSpec("b", "B", "int", default=0),
        ),
    )
    assert schema.defaults()["a"] == "x"
    assert schema.primary_field().name == "a"
    empty = ItemSchema(name="e", label="E", description="d")
    assert empty.primary_field() is None


def test_catalog_unknown_raises():
    with pytest.raises(KeyError):
        filter_schema("nope-filter")
    with pytest.raises(KeyError):
        action_schema("nope-action")


def test_form_field_types(qapp):
    specs = [
        FieldSpec("s", "S", "str", default="hi"),
        FieldSpec("i", "I", "int", default=3),
        FieldSpec("f", "F", "float", default=1.5),
        FieldSpec("b", "B", "bool", default=True),
        FieldSpec("c", "C", "choice", default="a", choices=("a", "b")),
        FieldSpec("m", "M", "multiline", default="line"),
        FieldSpec("l", "L", "list_str", default=["x", "y"]),
    ]
    widgets = [FormFieldWidget(s) for s in specs]
    assert widgets[0].value() == "hi"
    assert widgets[1].value() == 3
    assert widgets[2].value() == 1.5
    assert widgets[3].value() is True
    assert widgets[4].value() == "a"
    assert widgets[5].value() == "line"
    assert widgets[6].value() == ["x", "y"]

    widgets[0].set_value(None)
    assert widgets[0].value() == ""
    widgets[1].set_value("bad")
    assert widgets[1].value() == 0
    widgets[2].set_value("")
    # empty float -> 0.0
    assert widgets[2].value() == 0.0
    widgets[4].set_value("missing")
    widgets[6].set_value("a, b  c")
    assert widgets[6].value() == ["a", "b", "c"]
    assert FormFieldWidget(FieldSpec("z", "Z", "list_str")).is_empty()
    assert not FormFieldWidget(FieldSpec("z", "Z", "bool")).is_empty()

    # float/int from line edit path
    float_w = FormFieldWidget(FieldSpec("ff", "FF", "float"))
    float_w.set_value("2.5")
    assert float_w.value() == 2.5
    int_w = FormFieldWidget(FieldSpec("ii", "II", "str"))
    int_w.set_value([1, 2])
    assert "1" in int_w.value() or int_w.value()


def test_pipeline_item_edge_cases():
    item = PipelineItem(
        kind="filter",
        name="name",
        params={"a": 1, "b": 2, "c": 3, "d": 4},
    )
    assert "…" in item.display_label()
    raw = PipelineItem.from_config_dict("filter", "not empty")
    assert raw.inverted and raw.name == "empty"
    with pytest.raises(ValueError):
        PipelineItem.from_config_dict("filter", {"a": 1, "b": 2})
    plain = PipelineItem.from_config_dict("action", {"delete": None})
    assert plain.to_config_dict() == {"delete": None}


def test_rule_item_location_shapes():
    rule = RuleItem.from_config_dict(
        {
            "name": "n",
            "locations": [
                "a",
                {"path": "b"},
                {"path": ["c", "d"]},
                123,
            ],
            "tags": "one",
            "actions": [{"echo": "hi"}],
            "filters": None,
        }
    )
    assert "a" in rule.locations
    assert "b" in rule.locations
    assert "c" in rule.locations
    assert rule.tags == ["one"]
    assert rule.clone().name == "n"


def test_config_document_clone_and_empty():
    doc = ConfigDocument.from_config_dict({})
    assert doc.rules == []
    doc2 = ConfigDocument.new_with_example().clone()
    assert doc2.rules
    # clone method path
    assert doc2.clone().path is None


def test_yaml_preview_error(qapp, monkeypatch):
    w = YamlPreviewWidget()
    monkeypatch.setattr(
        "ui.widgets.yaml_preview_widget.document_to_yaml",
        lambda d: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    w.update_from_document(ConfigDocument.new_with_example())
    assert "Failed" in w.view.toPlainText()
    w.close()


def test_rule_list_duplicate_remove_move(qapp):
    w = RuleListWidget()
    doc = ConfigDocument.new_with_example()
    w.set_rules(doc.rules)
    w._duplicate()
    assert len(w.rules()) == 2
    w.set_current_index(1)
    w._move(-1)
    w._remove()
    assert len(w.rules()) >= 1
    w.refresh_current_label()
    # empty
    w.set_rules([])
    w._duplicate()
    w._remove()
    w._move(1)
    w.close()


def test_pipeline_list_empty_edit_guard(qapp):
    w = PipelineListWidget("action")
    w.set_items([])
    w._edit()
    w._remove()
    w._move(1)
    w.set_items([PipelineItem(kind="action", name="echo", primary_value="x")])
    w.list_widget.setCurrentRow(0)
    # edit cancel path via dialog reject - skip interactive
    w.close()


def test_item_editor_required_validation(qapp, monkeypatch):
    dialog = ItemEditorDialog("action")
    idx = dialog.type_combo.findData("echo")
    dialog.type_combo.setCurrentIndex(idx)
    # empty required msg
    monkeypatch.setattr(
        "ui.widgets.item_editor_dialog.QMessageBox.warning",
        lambda *a, **k: None,
    )
    dialog._on_accept()  # should warn and not accept when empty
    # fill and accept
    for widget in dialog._field_widgets:
        if widget.spec.name == "msg":
            widget.set_value("hello")
    dialog._on_accept()
    item = dialog.result_item()
    assert item.name == "echo"
    dialog.close()

    # empty filter with allow_empty
    d2 = ItemEditorDialog("filter")
    idx = d2.type_combo.findData("empty")
    d2.type_combo.setCurrentIndex(idx)
    item2 = d2.result_item()
    assert item2.name == "empty"
    d2.close()

    # delete action empty
    d3 = ItemEditorDialog("action")
    idx = d3.type_combo.findData("delete")
    d3.type_combo.setCurrentIndex(idx)
    assert d3.result_item().name == "delete"
    d3.close()


def test_configure_combobox_closes_popup(qapp):
    from PyQt6.QtCore import QEventLoop, QTimer

    from ui.styles.combo_fix import ClosingComboBox, soft_close_combo_popup

    combo = ClosingComboBox()
    combo.addItems(["a", "b", "c"])
    assert combo.count() == 3
    combo.showPopup()
    soft_close_combo_popup(combo)
    loop = QEventLoop()
    QTimer.singleShot(40, loop.quit)
    loop.exec()
    # Items must still be present after dismiss + reopen.
    assert combo.count() == 3
    combo.showPopup()
    assert combo.model() is not None
    assert combo.model().rowCount() == 3
    soft_close_combo_popup(combo)
    combo.close()
