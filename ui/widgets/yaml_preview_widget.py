"""Read-only YAML preview of the current configuration."""

from __future__ import annotations

from typing import Optional

from PyQt6.QtWidgets import QLabel, QTextEdit, QVBoxLayout, QWidget

from ui.models.config_document import ConfigDocument
from ui.services.config_io import document_to_yaml


class YamlPreviewWidget(QWidget):
    """Shows the generated YAML for the open document."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 0)
        layout.setSpacing(8)

        hint = QLabel(
            "This is the config organize will run. Compatible with the CLI "
            "(organize sim / organize run)."
        )
        hint.setObjectName("HintLabel")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        self.view = QTextEdit()
        self.view.setObjectName("YamlView")
        self.view.setReadOnly(True)
        layout.addWidget(self.view)

    def update_from_document(self, document: ConfigDocument) -> None:
        """Refresh the preview from *document*."""
        try:
            text = document_to_yaml(document)
        except Exception as exc:  # noqa: BLE001
            text = f"# Failed to render YAML:\n# {exc}"
        if self.view.toPlainText() != text:
            # Keep scroll position when possible.
            scroll = self.view.verticalScrollBar()
            pos = scroll.value() if scroll is not None else 0
            self.view.setPlainText(text)
            if scroll is not None:
                scroll.setValue(pos)
