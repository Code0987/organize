"""Schemas for all organize actions supported by the interactive editor."""

from __future__ import annotations

from typing import Dict

from organize_gui.models.field_definition import FieldDefinition
from organize_gui.models.item_schema import ItemSchema

_CONFLICT_CHOICES = [
    "skip",
    "overwrite",
    "deduplicate",
    "trash",
    "rename_new",
    "rename_existing",
]

_CONFLICT_FIELDS = [
    FieldDefinition(
        "on_conflict",
        "On conflict",
        "choice",
        default="rename_new",
        choices=_CONFLICT_CHOICES,
        help_text="What to do if the destination already exists",
    ),
    FieldDefinition(
        "rename_template",
        "Rename template",
        "str",
        default="{name} {counter}{extension}",
        help_text="Template used when renaming on conflict",
    ),
]

_AUTODETECT = FieldDefinition(
    "autodetect_folder",
    "Autodetect folder",
    "bool",
    default=True,
    help_text="Treat destinations without extension as folders",
)

ACTION_SCHEMAS: Dict[str, ItemSchema] = {
    "echo": ItemSchema(
        name="echo",
        label="Echo",
        description="Print a message (supports placeholders)",
        fields=[
            FieldDefinition(
                "msg",
                "Message",
                "str",
                default="",
                help_text="Message to print; supports {placeholders}",
                is_primary=True,
            ),
        ],
        standalone=True,
    ),
    "move": ItemSchema(
        name="move",
        label="Move",
        description="Move a file or directory to a new location",
        fields=[
            FieldDefinition(
                "dest",
                "Destination",
                "path",
                required=True,
                default="",
                help_text="Destination path; trailing slash = keep name",
                is_primary=True,
            ),
            *_CONFLICT_FIELDS,
            _AUTODETECT,
        ],
    ),
    "copy": ItemSchema(
        name="copy",
        label="Copy",
        description="Copy a file or directory to a new location",
        fields=[
            FieldDefinition(
                "dest",
                "Destination",
                "path",
                required=True,
                default="",
                help_text="Destination path; trailing slash = keep name",
                is_primary=True,
            ),
            *_CONFLICT_FIELDS,
            _AUTODETECT,
            FieldDefinition(
                "continue_with",
                "Continue with",
                "choice",
                default="copy",
                choices=["copy", "original"],
                help_text="Whether next actions use the copy or the original path",
            ),
        ],
    ),
    "rename": ItemSchema(
        name="rename",
        label="Rename",
        description="Rename a file or directory (same folder)",
        fields=[
            FieldDefinition(
                "new_name",
                "New name",
                "str",
                required=True,
                default="",
                help_text="New filename; supports placeholders; no slashes",
                is_primary=True,
            ),
            *_CONFLICT_FIELDS,
        ],
    ),
    "delete": ItemSchema(
        name="delete",
        label="Delete",
        description="Permanently delete a file or directory (no recovery!)",
        fields=[],
    ),
    "trash": ItemSchema(
        name="trash",
        label="Trash",
        description="Move a file or directory to the system trash",
        fields=[],
    ),
    "confirm": ItemSchema(
        name="confirm",
        label="Confirm",
        description="Ask the user for confirmation before continuing",
        fields=[
            FieldDefinition(
                "msg",
                "Message",
                "str",
                default="Continue?",
                help_text="Confirmation prompt; supports placeholders",
                is_primary=True,
            ),
            FieldDefinition(
                "default",
                "Default yes",
                "bool",
                default=True,
            ),
        ],
        standalone=True,
    ),
    "write": ItemSchema(
        name="write",
        label="Write",
        description="Write text to a file",
        fields=[
            FieldDefinition(
                "text",
                "Text",
                "text",
                required=True,
                default="",
                help_text="Text to write; supports placeholders",
            ),
            FieldDefinition(
                "outfile",
                "Output file",
                "path",
                required=True,
                default="",
                help_text="File path to write into",
            ),
            FieldDefinition(
                "mode",
                "Mode",
                "choice",
                default="append",
                choices=["append", "prepend", "overwrite"],
            ),
            FieldDefinition("encoding", "Encoding", "str", default="utf-8"),
            FieldDefinition("newline", "Append newline", "bool", default=True),
            FieldDefinition(
                "clear_before_first_write",
                "Clear before first write",
                "bool",
                default=False,
            ),
        ],
        standalone=True,
    ),
    "shell": ItemSchema(
        name="shell",
        label="Shell",
        description="Run a shell command",
        fields=[
            FieldDefinition(
                "cmd",
                "Command",
                "text",
                required=True,
                default="",
                help_text="Shell command; supports placeholders",
                is_primary=True,
            ),
            FieldDefinition(
                "run_in_simulation",
                "Run in simulation",
                "bool",
                default=False,
            ),
            FieldDefinition(
                "ignore_errors",
                "Ignore errors",
                "bool",
                default=False,
            ),
            FieldDefinition(
                "simulation_output",
                "Simulation output",
                "str",
                default="** simulation **",
            ),
            FieldDefinition(
                "simulation_returncode",
                "Simulation return code",
                "int",
                default=0,
            ),
        ],
        standalone=True,
    ),
    "python": ItemSchema(
        name="python",
        label="Python",
        description="Run custom Python code as an action",
        fields=[
            FieldDefinition(
                "code",
                "Code",
                "text",
                required=True,
                default="",
                help_text="Python code to execute",
                is_primary=True,
            ),
            FieldDefinition(
                "run_in_simulation",
                "Run in simulation",
                "bool",
                default=False,
            ),
        ],
        standalone=True,
    ),
    "symlink": ItemSchema(
        name="symlink",
        label="Symlink",
        description="Create a symbolic link",
        fields=[
            FieldDefinition(
                "dest",
                "Destination",
                "path",
                required=True,
                default="",
                is_primary=True,
            ),
            *_CONFLICT_FIELDS,
            _AUTODETECT,
        ],
    ),
    "hardlink": ItemSchema(
        name="hardlink",
        label="Hardlink",
        description="Create a hard link",
        fields=[
            FieldDefinition(
                "dest",
                "Destination",
                "path",
                required=True,
                default="",
                is_primary=True,
            ),
            *_CONFLICT_FIELDS,
            _AUTODETECT,
        ],
    ),
    "macos_tags": ItemSchema(
        name="macos_tags",
        label="macOS tags",
        description="Set macOS Finder tags on a file",
        fields=[
            FieldDefinition(
                "tags",
                "Tags",
                "list_str",
                required=True,
                default=[],
                help_text="Comma-separated tag names to apply",
                is_primary=True,
            ),
        ],
    ),
}


def get_action_schema(name: str) -> ItemSchema:
    """Return the schema for an action name, or a generic fallback."""
    if name in ACTION_SCHEMAS:
        return ACTION_SCHEMAS[name]
    return ItemSchema(
        name=name,
        label=name,
        description=f"Unknown action '{name}' — edit parameters carefully",
        fields=[
            FieldDefinition(
                "value",
                "Value (YAML)",
                "text",
                default="",
                help_text="Raw value; advanced use only",
            ),
        ],
    )


def action_type_names() -> list[str]:
    """Return sorted action type names for UI combo boxes."""
    return sorted(ACTION_SCHEMAS.keys())
