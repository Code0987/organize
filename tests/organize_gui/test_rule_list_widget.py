"""Tests for RuleListWidget structural operations."""

from __future__ import annotations

import pytest

from organize_gui.models.action_data import ActionData
from organize_gui.models.rule_data import RuleData
from organize_gui.widgets.rule_list import RuleListWidget


@pytest.fixture()
def rule_list(qapp):
    widget = RuleListWidget()
    yield widget
    widget.close()
    widget.deleteLater()


class TestRuleListWidget:
    def test_set_rules_and_select(self, rule_list) -> None:
        rules = [
            RuleData.create_default(),
            RuleData(name="Second", actions=[ActionData.create_default("echo")]),
        ]
        rule_list.set_rules(rules, select_index=1)
        assert rule_list.current_index() == 1
        assert len(rule_list.rules()) == 2

    def test_add_remove(self, rule_list) -> None:
        rules: list = []
        rule_list.set_rules(rules)
        modified = []
        rule_list.rules_modified.connect(lambda: modified.append(True))
        rule_list._on_add()  # noqa: SLF001 — unit-test internal slot
        assert len(rule_list.rules()) == 1
        assert modified
        rule_list._on_remove()  # noqa: SLF001
        assert len(rule_list.rules()) == 0

    def test_move_up_down(self, rule_list) -> None:
        rules = [
            RuleData(name="A", actions=[ActionData.create_default("echo")]),
            RuleData(name="B", actions=[ActionData.create_default("echo")]),
        ]
        rule_list.set_rules(rules, select_index=1)
        rule_list._on_move_up()  # noqa: SLF001
        assert rule_list.rules()[0].name == "B"
        rule_list._on_move_down()  # noqa: SLF001
        assert rule_list.rules()[0].name == "A"
