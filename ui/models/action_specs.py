"""Interactive-editor schemas for every organize action."""

from __future__ import annotations

from typing import Dict

from ui.constants import CONFLICT_MODES
from ui.models.field_spec import FieldSpec
from ui.models.item_spec import ItemSpec

ACTION_SPECS: Dict[str, ItemSpec] = {
    "echo": ItemSpec(
        name="echo",
        title="Echo",
        summary="Print a message. Useful while designing a rule.",
        fields=(
            FieldSpec(
                "msg",
                "Message",
                "textarea",
                placeholder="Found {path.name}",
                hint="{path.name} is always available. {name} needs a name filter.",
                scalar=True,
            ),
        ),
        standalone=True,
    ),
    "move": ItemSpec(
        name="move",
        title="Move",
        summary="Move the file or folder. Trailing slash = keep the name.",
        fields=(
            FieldSpec(
                "dest",
                "Destination",
                "path",
                placeholder="~/Documents/PDF/",
                scalar=True,
            ),
            FieldSpec(
                "on_conflict",
                "On conflict",
                "choice",
                default="rename_new",
                choices=CONFLICT_MODES,
            ),
        ),
    ),
    "copy": ItemSpec(
        name="copy",
        title="Copy",
        summary="Copy the file or folder.",
        fields=(
            FieldSpec(
                "dest",
                "Destination",
                "path",
                placeholder="~/Backup/{extension}/",
                scalar=True,
            ),
            FieldSpec(
                "on_conflict",
                "On conflict",
                "choice",
                default="rename_new",
                choices=CONFLICT_MODES,
            ),
            FieldSpec(
                "continue_with",
                "Continue with",
                "choice",
                default="copy",
                choices=("copy", "original"),
            ),
        ),
    ),
    "rename": ItemSpec(
        name="rename",
        title="Rename",
        summary="Rename in place. Use {name}, {extension}, filter vars.",
        fields=(
            FieldSpec(
                "new_name",
                "New name",
                "text",
                placeholder="{created.year}-{name}{extension}",
                scalar=True,
            ),
            FieldSpec(
                "on_conflict",
                "On conflict",
                "choice",
                default="rename_new",
                choices=CONFLICT_MODES,
            ),
        ),
    ),
    "trash": ItemSpec(
        name="trash",
        title="Trash",
        summary="Move the file or folder to the system trash.",
    ),
    "delete": ItemSpec(
        name="delete",
        title="Delete",
        summary="Permanently delete. There is no undo.",
    ),
    "confirm": ItemSpec(
        name="confirm",
        title="Confirm",
        summary="Ask before continuing the action list.",
        fields=(
            FieldSpec("msg", "Message", "text", default="Continue?", scalar=True),
            FieldSpec("default", "Default yes", "bool", default=True),
        ),
        standalone=True,
    ),
    "write": ItemSpec(
        name="write",
        title="Write",
        summary="Append, prepend, or overwrite a text file.",
        fields=(
            FieldSpec("text", "Text", "textarea", placeholder="{path}"),
            FieldSpec("outfile", "Outfile", "path", placeholder="~/organize-log.txt"),
            FieldSpec(
                "mode",
                "Mode",
                "choice",
                default="append",
                choices=("append", "prepend", "overwrite"),
            ),
        ),
        standalone=True,
    ),
    "shell": ItemSpec(
        name="shell",
        title="Shell",
        summary="Run a shell command. Exposes {shell.output}.",
        fields=(
            FieldSpec("cmd", "Command", "textarea", placeholder="echo {path}", scalar=True),
            FieldSpec("run_in_simulation", "Run in simulation", "bool", default=False),
            FieldSpec("ignore_errors", "Ignore errors", "bool", default=False),
        ),
        standalone=True,
    ),
    "python": ItemSpec(
        name="python",
        title="Python",
        summary="Run a Python snippet against the current file.",
        fields=(
            FieldSpec("code", "Code", "textarea", placeholder="print(path)", scalar=True),
            FieldSpec("run_in_simulation", "Run in simulation", "bool", default=False),
        ),
        standalone=True,
    ),
    "hardlink": ItemSpec(
        name="hardlink",
        title="Hardlink",
        summary="Create a hard link at dest.",
        fields=(
            FieldSpec("dest", "Destination", "path", placeholder="~/Links/", scalar=True),
            FieldSpec(
                "on_conflict",
                "On conflict",
                "choice",
                default="rename_new",
                choices=CONFLICT_MODES,
            ),
        ),
    ),
    "symlink": ItemSpec(
        name="symlink",
        title="Symlink",
        summary="Create a symbolic link at dest.",
        fields=(
            FieldSpec("dest", "Destination", "path", placeholder="~/Links/", scalar=True),
            FieldSpec(
                "on_conflict",
                "On conflict",
                "choice",
                default="rename_new",
                choices=CONFLICT_MODES,
            ),
        ),
    ),
    "macos_tags": ItemSpec(
        name="macos_tags",
        title="macOS tags",
        summary="Set Finder tags (macOS only).",
        fields=(FieldSpec("tags", "Tags", "list", placeholder="Red, Work", scalar=True),),
    ),
}
