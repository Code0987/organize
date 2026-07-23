"""Catalog of interactive schemas for organize filters and actions.

The catalog is intentionally curated for the GUI: it covers the common
parameters users edit interactively, while still allowing advanced values
via the YAML preview/export path.
"""

from __future__ import annotations

from typing import Dict, List

from ui.schemas.field_spec import FieldSpec, ItemSchema

_TIME_FIELDS = (
    FieldSpec("years", "Years", "int", default=0),
    FieldSpec("months", "Months", "int", default=0),
    FieldSpec("weeks", "Weeks", "int", default=0),
    FieldSpec("days", "Days", "int", default=0),
    FieldSpec("hours", "Hours", "int", default=0),
    FieldSpec("minutes", "Minutes", "int", default=0),
    FieldSpec("seconds", "Seconds", "int", default=0),
    FieldSpec(
        "mode",
        "Mode",
        "choice",
        default="older",
        choices=("older", "newer"),
        help_text="'older' = before the offset, 'newer' = within the offset.",
    ),
    FieldSpec(
        "timezone",
        "Timezone",
        "str",
        default="local",
        help_text="Timezone name or 'local'.",
    ),
)

_CONFLICT_FIELD = FieldSpec(
    "on_conflict",
    "On conflict",
    "choice",
    default="rename_new",
    choices=(
        "skip",
        "overwrite",
        "deduplicate",
        "trash",
        "rename_new",
        "rename_existing",
    ),
)

_FILTER_SCHEMAS: Dict[str, ItemSchema] = {
    "extension": ItemSchema(
        name="extension",
        label="Extension",
        description="Match files by extension (e.g. pdf, jpg).",
        fields=(
            FieldSpec(
                "extensions",
                "Extensions",
                "list_str",
                required=True,
                is_primary=True,
                help_text="Space- or comma-separated extensions without dots.",
            ),
        ),
    ),
    "name": ItemSchema(
        name="name",
        label="Name",
        description="Match files/folders by name patterns.",
        fields=(
            FieldSpec("match", "Simple match", "str", help_text="simplematch pattern."),
            FieldSpec("startswith", "Starts with", "list_str"),
            FieldSpec("contains", "Contains", "list_str"),
            FieldSpec("endswith", "Ends with", "list_str"),
            FieldSpec("case_sensitive", "Case sensitive", "bool", default=True),
        ),
    ),
    "regex": ItemSchema(
        name="regex",
        label="Regex (filename)",
        description="Match filenames with a regular expression.",
        fields=(
            FieldSpec(
                "expr",
                "Expression",
                "str",
                required=True,
                is_primary=True,
                help_text="Python regular expression.",
            ),
        ),
    ),
    "filecontent": ItemSchema(
        name="filecontent",
        label="File content",
        description="Match file content with a regular expression.",
        fields=(
            FieldSpec(
                "expr",
                "Expression",
                "str",
                required=True,
                is_primary=True,
            ),
        ),
    ),
    "size": ItemSchema(
        name="size",
        label="Size",
        description="Match by size conditions (e.g. > 1 MB, < 10 KB).",
        fields=(
            FieldSpec(
                "conditions",
                "Conditions",
                "list_str",
                required=True,
                is_primary=True,
                help_text="One condition per item, e.g. '> 10 MB'.",
            ),
        ),
    ),
    "created": ItemSchema(
        name="created",
        label="Created",
        description="Match by file creation date.",
        fields=_TIME_FIELDS,
        allow_empty=True,
    ),
    "lastmodified": ItemSchema(
        name="lastmodified",
        label="Last modified",
        description="Match by last modified date.",
        fields=_TIME_FIELDS,
        allow_empty=True,
    ),
    "date_added": ItemSchema(
        name="date_added",
        label="Date added",
        description="Match by date added (macOS).",
        fields=_TIME_FIELDS,
        allow_empty=True,
    ),
    "date_lastused": ItemSchema(
        name="date_lastused",
        label="Date last used",
        description="Match by last used date (macOS).",
        fields=_TIME_FIELDS,
        allow_empty=True,
    ),
    "empty": ItemSchema(
        name="empty",
        label="Empty",
        description="Match empty files or folders.",
        allow_empty=True,
    ),
    "duplicate": ItemSchema(
        name="duplicate",
        label="Duplicate",
        description="Find duplicate files.",
        fields=(
            FieldSpec(
                "detect_original_by",
                "Detect original by",
                "choice",
                default="first_seen",
                choices=(
                    "first_seen",
                    "-first_seen",
                    "last_seen",
                    "-last_seen",
                    "name",
                    "-name",
                    "created",
                    "-created",
                    "lastmodified",
                    "-lastmodified",
                ),
            ),
            FieldSpec("hash_algorithm", "Hash algorithm", "str", default="sha1"),
        ),
        allow_empty=True,
    ),
    "hash": ItemSchema(
        name="hash",
        label="Hash",
        description="Compute a file hash (available as {hash}).",
        fields=(
            FieldSpec("algorithm", "Algorithm", "str", default="sha1", is_primary=True),
        ),
        allow_empty=True,
    ),
    "mimetype": ItemSchema(
        name="mimetype",
        label="MIME type",
        description="Match by MIME type.",
        fields=(
            FieldSpec(
                "mimetypes",
                "MIME types",
                "list_str",
                required=True,
                is_primary=True,
                help_text="e.g. image/jpeg, application/pdf",
            ),
        ),
    ),
    "exif": ItemSchema(
        name="exif",
        label="EXIF",
        description="Read EXIF tags (optionally filter by tags).",
        fields=(
            FieldSpec(
                "lowercase_keys",
                "Lowercase keys",
                "bool",
                default=True,
            ),
        ),
        allow_empty=True,
    ),
    "python": ItemSchema(
        name="python",
        label="Python",
        description="Custom Python expression/code filter.",
        fields=(
            FieldSpec(
                "code",
                "Code",
                "multiline",
                required=True,
                is_primary=True,
                help_text="Return True to keep the file.",
            ),
        ),
    ),
    "macos_tags": ItemSchema(
        name="macos_tags",
        label="macOS tags",
        description="Match macOS Finder tags.",
        fields=(
            FieldSpec("tags", "Tags", "list_str", required=True, is_primary=True),
        ),
    ),
}

_ACTION_SCHEMAS: Dict[str, ItemSchema] = {
    "echo": ItemSchema(
        name="echo",
        label="Echo",
        description="Print a message (supports placeholders).",
        fields=(
            FieldSpec("msg", "Message", "str", required=True, is_primary=True),
        ),
        supports_invert=False,
    ),
    "move": ItemSchema(
        name="move",
        label="Move",
        description="Move a file or folder to a destination.",
        fields=(
            FieldSpec("dest", "Destination", "str", required=True, is_primary=True),
            _CONFLICT_FIELD,
            FieldSpec(
                "rename_template",
                "Rename template",
                "str",
                default="{name} {counter}{extension}",
            ),
            FieldSpec("autodetect_folder", "Autodetect folder", "bool", default=True),
        ),
        supports_invert=False,
    ),
    "copy": ItemSchema(
        name="copy",
        label="Copy",
        description="Copy a file or folder to a destination.",
        fields=(
            FieldSpec("dest", "Destination", "str", required=True, is_primary=True),
            _CONFLICT_FIELD,
            FieldSpec(
                "rename_template",
                "Rename template",
                "str",
                default="{name} {counter}{extension}",
            ),
            FieldSpec("autodetect_folder", "Autodetect folder", "bool", default=True),
            FieldSpec(
                "continue_with",
                "Continue with",
                "choice",
                default="copy",
                choices=("copy", "original"),
            ),
        ),
        supports_invert=False,
    ),
    "rename": ItemSchema(
        name="rename",
        label="Rename",
        description="Rename a file or folder in place.",
        fields=(
            FieldSpec(
                "new_name",
                "New name",
                "str",
                required=True,
                is_primary=True,
                help_text="Template for the new name, e.g. '{name}_{now().date}'.",
            ),
            _CONFLICT_FIELD,
            FieldSpec(
                "rename_template",
                "Conflict rename template",
                "str",
                default="{name} {counter}{extension}",
            ),
        ),
        supports_invert=False,
    ),
    "delete": ItemSchema(
        name="delete",
        label="Delete",
        description="Permanently delete a file or folder.",
        allow_empty=True,
        supports_invert=False,
    ),
    "trash": ItemSchema(
        name="trash",
        label="Trash",
        description="Move a file or folder to the system trash.",
        allow_empty=True,
        supports_invert=False,
    ),
    "copy_path_write": ItemSchema(  # placeholder not used
        name="_unused",
        label="",
        description="",
        supports_invert=False,
    ),
    "write": ItemSchema(
        name="write",
        label="Write",
        description="Write text to a file.",
        fields=(
            FieldSpec("text", "Text", "multiline", required=True),
            FieldSpec("outfile", "Output file", "str", required=True),
            FieldSpec(
                "mode",
                "Mode",
                "choice",
                default="append",
                choices=("append", "prepend", "overwrite"),
            ),
            FieldSpec("encoding", "Encoding", "str", default="utf-8"),
            FieldSpec("newline", "Append newline", "bool", default=True),
            FieldSpec(
                "clear_before_first_write",
                "Clear before first write",
                "bool",
                default=False,
            ),
        ),
        supports_invert=False,
    ),
    "shell": ItemSchema(
        name="shell",
        label="Shell",
        description="Run a shell command.",
        fields=(
            FieldSpec("cmd", "Command", "str", required=True, is_primary=True),
            FieldSpec("run_in_simulation", "Run in simulation", "bool", default=False),
            FieldSpec("ignore_errors", "Ignore errors", "bool", default=False),
            FieldSpec("simulation_output", "Simulation output", "str", default=""),
            FieldSpec("simulation_returncode", "Simulation return code", "int", default=0),
        ),
        supports_invert=False,
    ),
    "python": ItemSchema(
        name="python",
        label="Python",
        description="Run Python code as an action.",
        fields=(
            FieldSpec("code", "Code", "multiline", required=True, is_primary=True),
            FieldSpec("run_in_simulation", "Run in simulation", "bool", default=False),
        ),
        supports_invert=False,
    ),
    "confirm": ItemSchema(
        name="confirm",
        label="Confirm",
        description="Ask for confirmation before continuing.",
        fields=(
            FieldSpec("msg", "Message", "str", required=True, is_primary=True),
            FieldSpec("default", "Default yes", "bool", default=True),
        ),
        supports_invert=False,
    ),
    "symlink": ItemSchema(
        name="symlink",
        label="Symlink",
        description="Create a symbolic link.",
        fields=(
            FieldSpec("dest", "Destination", "str", required=True, is_primary=True),
            _CONFLICT_FIELD,
            FieldSpec(
                "rename_template",
                "Rename template",
                "str",
                default="{name} {counter}{extension}",
            ),
            FieldSpec("autodetect_folder", "Autodetect folder", "bool", default=True),
        ),
        supports_invert=False,
    ),
    "hardlink": ItemSchema(
        name="hardlink",
        label="Hardlink",
        description="Create a hard link.",
        fields=(
            FieldSpec("dest", "Destination", "str", required=True, is_primary=True),
            _CONFLICT_FIELD,
            FieldSpec(
                "rename_template",
                "Rename template",
                "str",
                default="{name} {counter}{extension}",
            ),
            FieldSpec("autodetect_folder", "Autodetect folder", "bool", default=True),
        ),
        supports_invert=False,
    ),
    "macos_tags": ItemSchema(
        name="macos_tags",
        label="macOS tags",
        description="Add macOS Finder tags.",
        fields=(
            FieldSpec("tags", "Tags", "list_str", required=True, is_primary=True),
        ),
        supports_invert=False,
    ),
}

# Remove accidental placeholder if any
_ACTION_SCHEMAS.pop("copy_path_write", None)


def list_filter_names() -> List[str]:
    """Return sorted filter schema names available in the GUI."""
    return sorted(_FILTER_SCHEMAS.keys())


def list_action_names() -> List[str]:
    """Return sorted action schema names available in the GUI."""
    return sorted(_ACTION_SCHEMAS.keys())


def filter_schema(name: str) -> ItemSchema:
    """Look up a filter schema by name."""
    try:
        return _FILTER_SCHEMAS[name]
    except KeyError as exc:
        raise KeyError(f"Unknown filter schema: {name}") from exc


def action_schema(name: str) -> ItemSchema:
    """Look up an action schema by name."""
    try:
        return _ACTION_SCHEMAS[name]
    except KeyError as exc:
        raise KeyError(f"Unknown action schema: {name}") from exc
