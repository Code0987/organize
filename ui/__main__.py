"""Allow ``python -m ui`` to start the desktop application."""

from __future__ import annotations

from ui.app import run


def main() -> None:
    """Entry point for the organize desktop GUI."""
    raise SystemExit(run())


if __name__ == "__main__":
    main()
