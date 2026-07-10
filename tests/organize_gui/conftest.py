"""Fixtures shared by GUI unit tests."""

from __future__ import annotations

import os
import sys
from typing import Iterator

import pytest

# Must be set before any Qt import so headless CI/agents can construct widgets.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.fixture(scope="session")
def qapp() -> Iterator[object]:
    """Session-scoped QApplication for worker and widget tests.

    A full :class:`QApplication` is required for ``QWidget`` subclasses.
    Creating :class:`QCoreApplication` first would make later widget tests abort.
    """
    from PyQt6.QtWidgets import QApplication

    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


@pytest.fixture()
def sample_config_yaml() -> str:
    """Minimal valid organize config used across several tests."""
    return """
rules:
  - name: "Find PDFs"
    locations:
      - ~/Downloads
    subfolders: true
    filters:
      - extension: pdf
    actions:
      - echo: "Found PDF!"
"""
