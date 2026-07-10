"""Schemas for all organize filters supported by the interactive editor."""

from __future__ import annotations

from typing import Dict

from organize_gui.models.field_definition import FieldDefinition
from organize_gui.models.item_schema import ItemSchema

# Shared time-based fields used by created / lastmodified / date_* filters.
_TIME_FIELDS = [
    FieldDefinition("years", "Years", "int", default=0, help_text="Age in years"),
    FieldDefinition("months", "Months", "int", default=0),
    FieldDefinition("weeks", "Weeks", "int", default=0),
    FieldDefinition("days", "Days", "int", default=0),
    FieldDefinition("hours", "Hours", "int", default=0),
    FieldDefinition("minutes", "Minutes", "int", default=0),
    FieldDefinition("seconds", "Seconds", "int", default=0),
    FieldDefinition(
        "mode",
        "Mode",
        "choice",
        default="older",
        choices=["older", "newer"],
        help_text="Match older or newer than the given age",
    ),
    FieldDefinition(
        "timezone",
        "Timezone",
        "str",
        default="local",
        help_text="Timezone name or 'local'",
    ),
]

FILTER_SCHEMAS: Dict[str, ItemSchema] = {
    "extension": ItemSchema(
        name="extension",
        label="Extension",
        description="Match files by file extension (e.g. pdf, jpg)",
        fields=[
            FieldDefinition(
                "extensions",
                "Extensions",
                "list_str",
                default=[],
                help_text="Comma-separated extensions without the leading dot",
                is_primary=True,
            ),
        ],
        supports_dirs=False,
    ),
    "name": ItemSchema(
        name="name",
        label="Name",
        description="Match files and folders by name",
        fields=[
            FieldDefinition(
                "match",
                "Match pattern",
                "str",
                default="*",
                help_text="simplematch pattern (default: *)",
            ),
            FieldDefinition(
                "startswith",
                "Starts with",
                "list_str",
                default=[],
                help_text="Name must start with one of these (comma-separated)",
            ),
            FieldDefinition(
                "contains",
                "Contains",
                "list_str",
                default=[],
                help_text="Name must contain one of these (comma-separated)",
            ),
            FieldDefinition(
                "endswith",
                "Ends with",
                "list_str",
                default=[],
                help_text="Name (without extension) must end with one of these",
            ),
            FieldDefinition(
                "case_sensitive",
                "Case sensitive",
                "bool",
                default=True,
            ),
        ],
    ),
    "size": ItemSchema(
        name="size",
        label="Size",
        description="Match by file or folder size (e.g. '>= 500 MB', '< 20k')",
        fields=[
            FieldDefinition(
                "conditions",
                "Conditions",
                "list_str",
                default=[],
                help_text="Size constraints, e.g. '>= 500 MB' or '>20k, < 1 TB'",
                is_primary=True,
            ),
        ],
    ),
    "regex": ItemSchema(
        name="regex",
        label="Regex",
        description="Match filenames with a regular expression",
        fields=[
            FieldDefinition(
                "expr",
                "Expression",
                "str",
                required=True,
                default="",
                help_text="Regular expression; named groups become placeholders",
                is_primary=True,
            ),
        ],
    ),
    "empty": ItemSchema(
        name="empty",
        label="Empty",
        description="Match empty files or empty directories",
        fields=[],
    ),
    "created": ItemSchema(
        name="created",
        label="Created",
        description="Match by file creation date",
        fields=list(_TIME_FIELDS),
        supports_dirs=False,
    ),
    "lastmodified": ItemSchema(
        name="lastmodified",
        label="Last modified",
        description="Match by last modification date",
        fields=list(_TIME_FIELDS),
        supports_dirs=False,
    ),
    "date_added": ItemSchema(
        name="date_added",
        label="Date added",
        description="Match by date added (macOS)",
        fields=list(_TIME_FIELDS),
        supports_dirs=False,
    ),
    "date_lastused": ItemSchema(
        name="date_lastused",
        label="Date last used",
        description="Match by date last used (macOS)",
        fields=list(_TIME_FIELDS),
        supports_dirs=False,
    ),
    "duplicate": ItemSchema(
        name="duplicate",
        label="Duplicate",
        description="Detect duplicate files by content hash",
        fields=[
            FieldDefinition(
                "detect_original_by",
                "Detect original by",
                "choice",
                default="first_seen",
                choices=[
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
                ],
            ),
            FieldDefinition(
                "hash_algorithm",
                "Hash algorithm",
                "str",
                default="sha1",
            ),
        ],
        supports_dirs=False,
    ),
    "hash": ItemSchema(
        name="hash",
        label="Hash",
        description="Compute a file hash (always matches; useful for templates)",
        fields=[
            FieldDefinition(
                "algorithm",
                "Algorithm",
                "str",
                default="md5",
                is_primary=True,
            ),
        ],
        supports_dirs=False,
    ),
    "mimetype": ItemSchema(
        name="mimetype",
        label="MIME type",
        description="Match by MIME type",
        fields=[
            FieldDefinition(
                "mimetypes",
                "MIME types",
                "list_str",
                default=[],
                help_text="Comma-separated MIME types, e.g. image/jpeg, application/pdf",
                is_primary=True,
            ),
        ],
        supports_dirs=False,
    ),
    "filecontent": ItemSchema(
        name="filecontent",
        label="File content",
        description="Match text extracted from file content via regex",
        fields=[
            FieldDefinition(
                "expr",
                "Expression",
                "str",
                default="(?P<all>.*)",
                help_text="Regex applied to extracted text content",
                is_primary=True,
            ),
        ],
        supports_dirs=False,
    ),
    "exif": ItemSchema(
        name="exif",
        label="EXIF",
        description="Read EXIF metadata from images",
        fields=[],
        supports_dirs=False,
    ),
    "macos_tags": ItemSchema(
        name="macos_tags",
        label="macOS tags",
        description="Match files by macOS Finder tags",
        fields=[
            FieldDefinition(
                "tags",
                "Tags",
                "list_str",
                default=[],
                help_text="Comma-separated tag names",
                is_primary=True,
            ),
        ],
    ),
    "python": ItemSchema(
        name="python",
        label="Python",
        description="Custom Python expression as a filter",
        fields=[
            FieldDefinition(
                "code",
                "Code",
                "text",
                required=True,
                default="True",
                help_text="Python expression; truthy result means match",
                is_primary=True,
            ),
        ],
    ),
}


def get_filter_schema(name: str) -> ItemSchema:
    """Return the schema for a filter name, or a generic fallback."""
    if name in FILTER_SCHEMAS:
        return FILTER_SCHEMAS[name]
    return ItemSchema(
        name=name,
        label=name,
        description=f"Unknown filter '{name}' — edit parameters carefully",
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


def filter_type_names() -> list[str]:
    """Return sorted filter type names for UI combo boxes."""
    return sorted(FILTER_SCHEMAS.keys())
