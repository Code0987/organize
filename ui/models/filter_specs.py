"""Interactive-editor schemas for every organize filter."""

from __future__ import annotations

from typing import Dict

from ui.models.field_spec import FieldSpec
from ui.models.item_spec import ItemSpec

FILTER_SPECS: Dict[str, ItemSpec] = {
    "extension": ItemSpec(
        name="extension",
        title="Extension",
        summary="Match one or more file extensions.",
        fields=(
            FieldSpec(
                "extensions",
                "Extensions",
                "list",
                placeholder="pdf, jpg, png",
                hint="Comma-separated, with or without a leading dot.",
                scalar=True,
            ),
        ),
        dirs=False,
        can_invert=True,
    ),
    "name": ItemSpec(
        name="name",
        title="Name",
        summary="Match the file or folder name.",
        fields=(
            FieldSpec("match", "Match", "text", default="*", placeholder="Invoice-*"),
            FieldSpec("startswith", "Starts with", "list", placeholder="Invoice, Order"),
            FieldSpec("contains", "Contains", "list", placeholder="draft"),
            FieldSpec("endswith", "Ends with", "list", placeholder="_final"),
            FieldSpec("case_sensitive", "Case sensitive", "bool", default=True),
        ),
        can_invert=True,
    ),
    "regex": ItemSpec(
        name="regex",
        title="Regex",
        summary="Match the filename with a regular expression.",
        fields=(
            FieldSpec(
                "expr",
                "Expression",
                "text",
                placeholder=r"(?P<date>\d{4}-\d{2}-\d{2})",
                scalar=True,
            ),
        ),
        can_invert=True,
    ),
    "size": ItemSpec(
        name="size",
        title="Size",
        summary="Compare file or folder size.",
        fields=(
            FieldSpec(
                "size",
                "Constraint",
                "text",
                placeholder=">1MB, <20MB",
                hint="Examples: >1MB, <10KiB, >= 5 TB",
                scalar=True,
            ),
        ),
        can_invert=True,
    ),
    "created": ItemSpec(
        name="created",
        title="Created",
        summary="Match by creation date (falls back to ctime when birth time is unavailable).",
        fields=(
            FieldSpec("days", "Days", "int", default=0),
            FieldSpec("hours", "Hours", "int", default=0),
            FieldSpec("minutes", "Minutes", "int", default=0),
            FieldSpec(
                "mode",
                "Mode",
                "choice",
                default="older",
                choices=("older", "newer"),
            ),
        ),
        can_invert=True,
    ),
    "lastmodified": ItemSpec(
        name="lastmodified",
        title="Last modified",
        summary="Match by last-modified date.",
        fields=(
            FieldSpec("days", "Days", "int", default=0),
            FieldSpec("hours", "Hours", "int", default=0),
            FieldSpec("minutes", "Minutes", "int", default=0),
            FieldSpec(
                "mode",
                "Mode",
                "choice",
                default="older",
                choices=("older", "newer"),
            ),
        ),
        can_invert=True,
    ),
    "empty": ItemSpec(
        name="empty",
        title="Empty",
        summary="Match empty files or folders.",
        can_invert=True,
    ),
    "duplicate": ItemSpec(
        name="duplicate",
        title="Duplicate",
        summary="Detect duplicate files.",
        fields=(
            FieldSpec(
                "detect_original_by",
                "Original is",
                "choice",
                default="first_seen",
                choices=(
                    "first_seen",
                    "last_seen",
                    "name",
                    "created",
                    "lastmodified",
                ),
            ),
        ),
        can_invert=True,
    ),
    "filecontent": ItemSpec(
        name="filecontent",
        title="File content",
        summary="Regex against extracted text (txt, md, pdf, docx).",
        fields=(
            FieldSpec(
                "expr",
                "Expression",
                "textarea",
                placeholder=r"(?P<invoice>INV-\d+)",
                scalar=True,
            ),
        ),
        dirs=False,
        can_invert=True,
    ),
    "hash": ItemSpec(
        name="hash",
        title="Hash",
        summary="Compute a file hash and expose {hash}.",
        fields=(
            FieldSpec(
                "algorithm",
                "Algorithm",
                "choice",
                default="md5",
                choices=("md5", "sha1", "sha256", "sha512", "blake2b"),
                scalar=True,
            ),
        ),
        dirs=False,
        can_invert=True,
    ),
    "mimetype": ItemSpec(
        name="mimetype",
        title="MIME type",
        summary="Match a MIME type such as image or application/pdf.",
        fields=(
            FieldSpec(
                "mimetypes",
                "MIME types",
                "list",
                placeholder="image, application/pdf",
                scalar=True,
            ),
        ),
        dirs=False,
        can_invert=True,
    ),
    "exif": ItemSpec(
        name="exif",
        title="EXIF",
        summary="Read image / document metadata. Adds {exif} placeholders.",
        dirs=False,
        can_invert=True,
    ),
    "python": ItemSpec(
        name="python",
        title="Python",
        summary="Keep the file when the snippet returns a truthy value.",
        fields=(
            FieldSpec(
                "code",
                "Code",
                "textarea",
                placeholder="return path.stat().st_size > 0",
                scalar=True,
            ),
        ),
        can_invert=True,
    ),
    "macos_tags": ItemSpec(
        name="macos_tags",
        title="macOS tags",
        summary="Match Finder tags (macOS only).",
        fields=(FieldSpec("tags", "Tags", "list", placeholder="Red, Work", scalar=True),),
        can_invert=True,
    ),
    "date_added": ItemSpec(
        name="date_added",
        title="Date added",
        summary="macOS only — when the file was added to the folder.",
        fields=(
            FieldSpec("days", "Days", "int", default=0),
            FieldSpec(
                "mode",
                "Mode",
                "choice",
                default="older",
                choices=("older", "newer"),
            ),
        ),
        can_invert=True,
    ),
    "date_lastused": ItemSpec(
        name="date_lastused",
        title="Date last used",
        summary="macOS only — last used date.",
        fields=(
            FieldSpec("days", "Days", "int", default=0),
            FieldSpec(
                "mode",
                "Mode",
                "choice",
                default="older",
                choices=("older", "newer"),
            ),
        ),
        can_invert=True,
    ),
}
