"""Wheel events must not change unfocused dropdowns in the rule editor."""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

pytest.importorskip("PyQt6")

from PyQt6.QtCore import QPoint, QPointF, Qt
from PyQt6.QtGui import QWheelEvent
from PyQt6.QtWidgets import QApplication

from ui.widgets.scroll_combo_box import ScrollComboBox
from ui.widgets.scroll_spin_box import ScrollSpinBox


@pytest.fixture(scope="module")
def qapp() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def _wheel(widget) -> QWheelEvent:
    pos = QPointF(widget.rect().center())
    return QWheelEvent(
        pos,
        QPointF(widget.mapToGlobal(pos.toPoint())),
        QPoint(0, 0),
        QPoint(0, 120),
        Qt.MouseButton.NoButton,
        Qt.KeyboardModifier.NoModifier,
        Qt.ScrollPhase.NoScrollPhase,
        False,
    )


def test_combo_wheel_does_not_change_closed_list(qapp: QApplication) -> None:
    combo = ScrollComboBox()
    combo.addItems(["files", "dirs"])
    combo.setCurrentIndex(0)
    combo.wheelEvent(_wheel(combo))
    assert combo.currentText() == "files"
    combo.close()


def test_spin_wheel_does_not_change_unfocused(qapp: QApplication) -> None:
    spin = ScrollSpinBox()
    spin.setValue(3)
    spin.clearFocus()
    spin.wheelEvent(_wheel(spin))
    assert spin.value() == 3
    spin.close()
