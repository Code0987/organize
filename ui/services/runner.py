"""Execute an in-memory organize config (simulate or live)."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Callable, Optional

from organize import Config

from ui.models.config_document import ConfigDocument
from ui.services.capture_output import CaptureOutput, LogEntry
from ui.services.config_io import document_to_yaml


def run_document(
    document: ConfigDocument,
    *,
    simulate: bool = True,
    working_dir: Optional[Path] = None,
    on_entry: Optional[Callable[[LogEntry], None]] = None,
    auto_confirm: bool = True,
) -> CaptureOutput:
    """Run or simulate *document* and return the captured output.

    The process working directory is restored after execution so the GUI
    process is not left in a surprising cwd.
    """
    yaml_text = document_to_yaml(document)
    config = Config.from_string(yaml_text, config_path=document.path)
    output = CaptureOutput(on_entry=on_entry, auto_confirm=auto_confirm)

    previous_cwd = Path.cwd()
    work = (working_dir or previous_cwd).expanduser().resolve()
    try:
        config.execute(
            simulate=simulate,
            output=output,
            working_dir=work,
        )
    finally:
        os.chdir(previous_cwd)

    return output
