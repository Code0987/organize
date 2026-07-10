"""Allow running the GUI with ``python -m organize_gui``."""

from __future__ import annotations

import sys

from organize_gui.app import run_app


def main() -> None:
    """Entry point for ``python -m organize_gui`` and the ``organize-gui`` console script."""
    raise SystemExit(run_app())


if __name__ == "__main__":
    main()
