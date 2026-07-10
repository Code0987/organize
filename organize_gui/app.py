"""Application bootstrap for the organize PyQt6 GUI."""

from __future__ import annotations

import sys
from typing import List, Optional

from PyQt6.QtWidgets import QApplication

from organize_gui.main_window import MainWindow


def run_app(argv: Optional[List[str]] = None) -> int:
    """Create the Qt application, show the main window, and start the event loop.

    Args:
        argv: Optional argument list (defaults to ``sys.argv``).

    Returns:
        Process exit code from ``QApplication.exec()``.
    """
    args = list(sys.argv if argv is None else argv)
    app = QApplication(args)
    app.setApplicationName("organize")
    app.setOrganizationName("organize")
    app.setApplicationDisplayName("organize Rule Editor")

    window = MainWindow()

    # Optional: open a config path passed as the first argument
    if len(args) > 1 and not args[1].startswith("-"):
        from pathlib import Path

        from organize_gui.services.config_service import ConfigService

        path = Path(args[1])
        if path.is_file():
            try:
                document = ConfigService.load_path(path)
                window._load_document(document)  # noqa: SLF001 — intentional bootstrap
                window._log_panel.append(f"Opened {path}", level="system")  # noqa: SLF001
            except Exception as exc:  # noqa: BLE001
                window._log_panel.append(f"Failed to open {path}: {exc}", level="error")  # noqa: SLF001

    window.show()
    return app.exec()
