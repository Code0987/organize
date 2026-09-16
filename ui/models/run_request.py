"""Parameters for one background organize run."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Set


@dataclass
class RunRequest:
    """Everything :class:`OrganizeWorker` needs to call ``Config.execute``.

    Attributes:
        text: YAML config contents.
        config_path: Optional path used in organize's start event.
        simulate: ``True`` for dry-run (no filesystem writes).
        working_dir: Directory organize ``chdir``s into for the run.
        tags: Only run rules that have one of these tags.
        skip_tags: Skip rules that have one of these tags.
    """

    text: str
    config_path: Optional[Path]
    simulate: bool
    working_dir: Path
    tags: Set[str] = field(default_factory=set)
    skip_tags: Set[str] = field(default_factory=set)
