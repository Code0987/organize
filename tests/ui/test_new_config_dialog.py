"""New Config dialog should list presets without overlapping rows."""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

pytest.importorskip("PyQt6.QtWidgets")

from PyQt6.QtWidgets import QApplication

from ui.models.preset_library import PresetLibrary
from ui.widgets.new_config_dialog import NewConfigDialog


@pytest.fixture(scope="module")
def qapp() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_preset_rows_have_non_overlapping_heights(qapp: QApplication) -> None:
    dialog = NewConfigDialog()
    dialog.resize(560, 520)
    dialog.show()
    qapp.processEvents()
    dialog._sync_row_sizes()

    bottoms = []
    for index in range(dialog.list.count()):
        item = dialog.list.item(index)
        assert item is not None
        height = item.sizeHint().height()
        assert height >= 56
        rect = dialog.list.visualItemRect(item)
        for previous in bottoms:
            assert rect.top() >= previous, "preset rows overlap"
        bottoms.append(rect.bottom())

    assert dialog.list.count() == len(PresetLibrary().all())
    dialog.close()
