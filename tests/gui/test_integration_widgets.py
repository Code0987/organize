"""Integration tests for interactive editor dialogs and list widgets."""

from __future__ import annotations

import pytest

from ui.models.pipeline_item import PipelineItem
from ui.schemas.catalog import action_schema, filter_schema, list_action_names, list_filter_names
from ui.widgets.item_editor_dialog import ItemEditorDialog
from ui.widgets.location_list_widget import LocationListWidget
from ui.widgets.pipeline_list_widget import PipelineListWidget


pytestmark = pytest.mark.usefixtures("qapp")


def test_catalog_covers_core_filters_and_actions():
    filters = set(list_filter_names())
    actions = set(list_action_names())
    for name in ("extension", "name", "size", "created", "regex"):
        assert name in filters
        schema = filter_schema(name)
        assert schema.name == name
        assert schema.label
    for name in ("echo", "move", "copy", "rename", "trash", "delete"):
        assert name in actions
        schema = action_schema(name)
        assert schema.name == name


def test_item_editor_builds_extension_filter(qapp):
    dialog = ItemEditorDialog("filter")
    # Select extension type
    idx = dialog.type_combo.findData("extension")
    assert idx >= 0
    dialog.type_combo.setCurrentIndex(idx)
    # Fill primary list field
    assert dialog._field_widgets
    field = dialog._field_widgets[0]
    field.set_value("pdf jpg")
    item = dialog.result_item()
    assert item.kind == "filter"
    assert item.name == "extension"
    # primary shorthand or params
    if item.primary_value is not None:
        assert "pdf" in str(item.primary_value) or (
            isinstance(item.primary_value, list) and "pdf" in item.primary_value
        )
    else:
        assert "extensions" in item.params
    dialog.close()


def test_item_editor_builds_move_action(qapp):
    dialog = ItemEditorDialog("action")
    idx = dialog.type_combo.findData("move")
    assert idx >= 0
    dialog.type_combo.setCurrentIndex(idx)
    # dest is required primary
    for widget in dialog._field_widgets:
        if widget.spec.name == "dest":
            widget.set_value("~/Documents/PDFs/")
            break
    else:
        pytest.fail("dest field not found")
    item = dialog.result_item()
    assert item.name == "move"
    assert item.primary_value == "~/Documents/PDFs/" or item.params.get("dest")
    dialog.close()


def test_item_editor_edit_existing_inverted_filter(qapp):
    existing = PipelineItem(
        kind="filter",
        name="extension",
        primary_value="txt",
        inverted=True,
    )
    dialog = ItemEditorDialog("filter", item=existing)
    assert dialog.invert_check.isChecked()
    item = dialog.result_item()
    assert item.inverted is True
    assert item.name == "extension"
    dialog.close()


def test_pipeline_list_add_remove_reorder(qapp):
    widget = PipelineListWidget("filter")
    widget.set_items(
        [
            PipelineItem(kind="filter", name="extension", primary_value="pdf"),
            PipelineItem(kind="filter", name="empty"),
            PipelineItem(kind="filter", name="name", params={"startswith": "A"}),
        ]
    )
    assert len(widget.items()) == 3
    widget.list_widget.setCurrentRow(0)
    widget._move(1)
    names = [i.name for i in widget.items()]
    assert names[0] == "empty"
    assert names[1] == "extension"
    widget.list_widget.setCurrentRow(0)
    widget._remove()
    assert len(widget.items()) == 2
    widget.close()


def test_location_list_add_and_remove(qapp, tmp_path):
    widget = LocationListWidget()
    widget.set_locations([])
    assert widget.locations() == []
    widget.set_locations([str(tmp_path), str(tmp_path / "sub")])
    assert len(widget.locations()) == 2
    widget.list_widget.setCurrentRow(0)
    widget._remove()
    assert len(widget.locations()) == 1
    widget.close()
