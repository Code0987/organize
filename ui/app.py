"""Application entry point for the organize PyQt6 GUI."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import List, Optional

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtWidgets import QApplication, QMessageBox

from ui import ORGANIZE_VERSION
from ui.constants import APP_NAME, ORG_NAME
from ui.high_dpi import HighDpi
from ui.widgets.app_icon import AppIcon
from ui.widgets.main_window import MainWindow
from ui.widgets.theme import Theme


class OrganizeApp:
    """Create the QApplication, apply theming, and show the main window."""

    def __init__(self, argv: Optional[List[str]] = None) -> None:
        # Scale must be applied before QApplication, otherwise Qt paints at 1×
        # and Windows/WSLg stretches the bitmap (tiny + blurry).
        HighDpi().apply()
        QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )
        self.argv = list(sys.argv if argv is None else argv)
        self.qt = QApplication(self.argv)
        self.qt.setApplicationName(APP_NAME)
        self.qt.setOrganizationName(ORG_NAME)
        self.qt.setApplicationVersion(ORGANIZE_VERSION)
        Theme().apply(self.qt)
        self.qt.setWindowIcon(AppIcon().build())
        self.window = MainWindow()

    def run(self) -> int:
        """Show the window and enter the Qt event loop."""
        self.window.show()
        leftover = [arg for arg in self.argv[1:] if not arg.startswith("-")]
        if leftover:
            path = Path(leftover[0]).expanduser()
            if path.is_file():
                self.window.open_path(path)
            else:
                QMessageBox.warning(
                    self.window, "Not found", f"Config not found:\n{path}"
                )
        return self.qt.exec()


def main(argv: Optional[List[str]] = None) -> int:
    """Console-script entry point used by ``organize-gui`` and ``python -m ui``."""
    import sys as _sys
    import traceback

    def _excepthook(exc_type, exc, tb) -> None:
        """Keep the window alive if a slot raises; show the error instead."""
        text = "".join(traceback.format_exception(exc_type, exc, tb))
        try:
            QMessageBox.critical(None, "organize error", text[-4000:])
        except Exception:
            _sys.stderr.write(text)

    _sys.excepthook = _excepthook
    return OrganizeApp(argv).run()


if __name__ == "__main__":
    raise SystemExit(main())
