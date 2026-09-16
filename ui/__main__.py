"""Allow ``python -m ui`` to start the desktop application."""

from ui.app import main

if __name__ == "__main__":
    raise SystemExit(main())
