"""Tests for DynamicForm widget value round-trips."""

from __future__ import annotations

import pytest

from organize_gui.models.field_definition import FieldDefinition
from organize_gui.widgets.dynamic_form import DynamicForm


@pytest.fixture()
def form(qapp):
    """Create a DynamicForm bound to the session QApplication."""
    widget = DynamicForm()
    yield widget
    widget.close()
    widget.deleteLater()


class TestDynamicForm:
    def test_str_and_bool_and_int_round_trip(self, form: DynamicForm) -> None:
        fields = [
            FieldDefinition("name", "Name", "str", default=""),
            FieldDefinition("enabled", "Enabled", "bool", default=False),
            FieldDefinition("count", "Count", "int", default=0),
        ]
        form.set_fields(fields, {"name": "abc", "enabled": True, "count": 7})
        values = form.get_values()
        assert values["name"] == "abc"
        assert values["enabled"] is True
        assert values["count"] == 7

    def test_list_str_comma_separated(self, form: DynamicForm) -> None:
        fields = [
            FieldDefinition("extensions", "Extensions", "list_str", default=[]),
        ]
        form.set_fields(fields, {"extensions": ["pdf", "jpg"]})
        values = form.get_values()
        assert values["extensions"] == ["pdf", "jpg"]

    def test_choice_field(self, form: DynamicForm) -> None:
        fields = [
            FieldDefinition(
                "mode",
                "Mode",
                "choice",
                default="older",
                choices=["older", "newer"],
            ),
        ]
        form.set_fields(fields, {"mode": "newer"})
        assert form.get_values()["mode"] == "newer"

    def test_empty_fields_message(self, form: DynamicForm) -> None:
        form.set_fields([], {})
        assert form.get_values() == {}

    def test_text_field(self, form: DynamicForm) -> None:
        fields = [FieldDefinition("code", "Code", "text", default="")]
        form.set_fields(fields, {"code": "print(1)\nprint(2)"})
        assert "print(1)" in form.get_values()["code"]

    def test_values_changed_signal(self, form: DynamicForm) -> None:
        fields = [FieldDefinition("msg", "Msg", "str", default="")]
        form.set_fields(fields, {"msg": ""})
        seen = []
        form.values_changed.connect(lambda: seen.append(True))
        from PyQt6.QtWidgets import QLineEdit

        line = form.findChild(QLineEdit)
        assert line is not None
        line.setText("changed")
        assert seen
        assert form.get_values()["msg"] == "changed"
