from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List, Union

import pytest

from organize.output import SavingOutput

ORGANIZE_DIR = Path(__file__).parent.parent


@pytest.fixture()
def testoutput() -> SavingOutput:
    return SavingOutput()


def equal_items(a: Iterable, b: Iterable) -> bool:
    return Counter(a) == Counter(b)


def make_files(structure: Union[Dict, List], path: Union[Path, str] = "."):
    """Example structure:

    {
        "folder": {
            "subfolder": {
                "test.txt": "",
                "other.pdf": b"binary",
            },
        },
        "file.txt": "Hello world\nAnother line",
    }
    """
    if isinstance(path, str):
        path = Path(path)
    path.mkdir(parents=True, exist_ok=True)

    # structure is a list of filenames
    if isinstance(structure, list):
        for name in structure:
            (path / name).touch()
        return

    # structure is a dict
    for name, content in structure.items():
        resource: Path = path / name

        # folders are dicts
        if isinstance(content, dict):
            make_files(structure=content, path=resource)

        # everything else is a file
        elif content is None:
            resource.touch()
        elif isinstance(content, bytes):
            resource.write_bytes(content)
        elif isinstance(content, str):
            resource.write_text(content)
        else:
            raise ValueError(f"Unknown file data {content}")


def read_files(path: Union[Path, str] = "."):
    if isinstance(path, str):
        path = Path(path)

    result = dict()
    for x in path.glob("*"):
        if x.is_file():
            result[x.name] = x.read_text()
        if x.is_dir():
            result[x.name] = read_files(x)
    return result


# ----- GUI fixtures (merged here so nested tests/gui/conftest cannot shadow
# ``from conftest import make_files`` used across the suite) -----
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("ORGANIZE_UI_SCALE", "1")
os.environ.setdefault("ORGANIZE_THEME", "light")
os.environ.setdefault("ORGANIZE_SKIP_HOST_PROBES", "1")


@pytest.fixture(scope="session")
def qapp():
    """Session-scoped QApplication used by GUI tests."""
    from PyQt6.QtCore import Qt
    from PyQt6.QtGui import QGuiApplication
    from PyQt6.QtWidgets import QApplication

    from ui.styles.palette import ThemeMode
    from ui.styles.theme import apply_theme

    os.environ.setdefault("QT_SCALE_FACTOR", "1")
    QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication.instance()
    if app is None:
        app = QApplication(["organize-ui-tests"])
    apply_theme(app, ThemeMode.LIGHT)
    yield app


@pytest.fixture()
def main_window(qapp):
    """Fresh MainWindow for each GUI test."""
    from PyQt6.QtGui import QCloseEvent

    from ui.main_window import MainWindow

    window = MainWindow()
    yield window
    window.document.mark_clean()
    window._worker = None

    def _accept(event: QCloseEvent) -> None:
        event.accept()

    window.closeEvent = _accept  # type: ignore[method-assign]
    window.close()


@pytest.fixture()
def sample_tree(tmp_path: Path) -> Path:
    """Small file tree for organize dry-run / live GUI tests."""
    downloads = tmp_path / "Downloads"
    downloads.mkdir()
    (downloads / "invoice.pdf").write_text("pdf-bytes", encoding="utf-8")
    (downloads / "notes.txt").write_text("hello", encoding="utf-8")
    (downloads / "photo.JPG").write_text("img", encoding="utf-8")
    (tmp_path / "Documents").mkdir()
    return tmp_path

