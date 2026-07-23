"""Application bootstrap for the organize desktop GUI."""

from __future__ import annotations

import sys
from typing import List, Optional

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtWidgets import QApplication

from ui.main_window import MainWindow
from ui.styles.dpi import configure_process_dpi
from ui.styles.palette import ThemeMode
from ui.styles.system_theme import ThemeWatcher, detect_system_theme
from ui.styles.theme import apply_theme, current_theme_mode


def run(argv: Optional[List[str]] = None) -> int:
    """Create the Qt application and show the main window."""
    # MUST run before QApplication: injects QT_SCALE_FACTOR from Windows DPI.
    injected = configure_process_dpi()
    QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    args = list(sys.argv if argv is None else argv)
    app = QApplication(args)
    app.setApplicationName("Organize")
    app.setOrganizationName("organize")

    initial_mode = detect_system_theme()
    scale = apply_theme(app, initial_mode)

    dpr = 1.0
    screen = app.primaryScreen()
    if screen is not None:
        dpr = float(screen.devicePixelRatio())

    print(
        "Organize GUI: "
        f"theme={initial_mode.value}, "
        f"effective_scale={scale:.2f}, "
        f"qt_scale_factor={injected if injected is not None else 'unset'}, "
        f"devicePixelRatio={dpr:.2f}",
        file=sys.stderr,
    )

    window = MainWindow()

    def _on_theme_changed(mode: object) -> None:
        if not isinstance(mode, ThemeMode):
            return
        apply_theme(app, mode)
        # Force style refresh on the open window tree.
        window.style().unpolish(window)
        window.style().polish(window)
        window.update()
        if hasattr(window, "status_label"):
            window.status_label.setText(
                f"Theme → {mode.value} · scale {scale:.0%} · dpr {dpr:.2f}"
            )

    watcher = ThemeWatcher(app)
    watcher.theme_changed.connect(_on_theme_changed)
    # Keep a reference for the app lifetime.
    app.setProperty("theme_watcher", watcher)

    if hasattr(window, "status_label"):
        window.status_label.setText(
            f"Ready — {current_theme_mode(app).value} theme · "
            f"scale {scale:.0%} (dpr {dpr:.2f})"
        )
    window.show()
    return app.exec()
