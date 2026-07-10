"""Tests for ActionData YAML conversion."""

from __future__ import annotations

from organize_gui.models.action_data import ActionData


class TestActionDataRoundTrip:
    def test_echo_shorthand(self) -> None:
        action = ActionData.from_yaml_value({"echo": "Hello {path.name}"})
        assert action.name == "echo"
        assert action.params["msg"] == "Hello {path.name}"
        assert action.to_yaml_value() == {"echo": "Hello {path.name}"}

    def test_move_with_options(self) -> None:
        action = ActionData.from_yaml_value(
            {
                "move": {
                    "dest": "~/Documents/",
                    "on_conflict": "overwrite",
                }
            }
        )
        assert action.name == "move"
        assert action.params["dest"] == "~/Documents/"
        assert action.params["on_conflict"] == "overwrite"
        out = action.to_yaml_value()
        assert isinstance(out, dict)
        body = out["move"]
        assert body["dest"] == "~/Documents/"
        assert body["on_conflict"] == "overwrite"

    def test_move_shorthand_string(self) -> None:
        action = ActionData.from_yaml_value({"move": "~/Archive/"})
        assert action.params["dest"] == "~/Archive/"
        # Defaults omitted → shorthand back to string dest
        out = action.to_yaml_value()
        assert out == {"move": "~/Archive/"}

    def test_delete_no_params(self) -> None:
        action = ActionData.from_yaml_value("delete")
        assert action.name == "delete"
        assert action.to_yaml_value() == "delete"

    def test_trash_string(self) -> None:
        action = ActionData.from_yaml_value("trash")
        assert action.name == "trash"

    def test_write_full(self) -> None:
        action = ActionData.from_yaml_value(
            {
                "write": {
                    "text": "line",
                    "outfile": "~/log.txt",
                    "mode": "overwrite",
                }
            }
        )
        assert action.name == "write"
        assert action.params["text"] == "line"
        assert action.params["outfile"] == "~/log.txt"
        assert action.params["mode"] == "overwrite"

    def test_shell_action(self) -> None:
        action = ActionData.from_yaml_value({"shell": "echo hi"})
        assert action.name == "shell"
        assert action.params["cmd"] == "echo hi"

    def test_create_default(self) -> None:
        action = ActionData.create_default("echo")
        assert action.name == "echo"
        assert "msg" in action.params

    def test_display_label(self) -> None:
        action = ActionData(name="echo", params={"msg": "hi there"})
        assert "hi there" in action.display_label()
