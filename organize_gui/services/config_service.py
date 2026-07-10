"""Load, save, validate and serialize organize configuration documents."""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple

import yaml

from organize import Config, ConfigError
from organize_gui.models.config_document import ConfigDocument


class ConfigService:
    """Service for reading and writing organize YAML configs."""

    @staticmethod
    def load_path(path: Path) -> ConfigDocument:
        """Load a config document from a filesystem path.

        Args:
            path: Path to a YAML config file.

        Returns:
            Parsed :class:`ConfigDocument`.

        Raises:
            FileNotFoundError: If the path does not exist.
            ValueError: If the YAML structure is invalid for the editor.
            yaml.YAMLError: If the file is not valid YAML.
        """
        text = path.read_text(encoding="utf-8")
        return ConfigService.load_string(text, source_path=path)

    @staticmethod
    def load_string(
        text: str,
        source_path: Optional[Path] = None,
    ) -> ConfigDocument:
        """Parse a YAML string into a config document.

        Args:
            text: YAML configuration text.
            source_path: Optional origin path stored on the document.

        Returns:
            Parsed :class:`ConfigDocument`.
        """
        data = yaml.safe_load(text)
        return ConfigDocument.from_yaml_dict(data, source_path=source_path)

    @staticmethod
    def to_yaml(document: ConfigDocument) -> str:
        """Serialize a config document to a YAML string.

        Args:
            document: Document to serialize.

        Returns:
            YAML text suitable for saving or executing.
        """
        data = document.to_yaml_dict()
        return yaml.dump(
            data,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
            width=100,
        )

    @staticmethod
    def save(document: ConfigDocument, path: Optional[Path] = None) -> Path:
        """Write a config document to disk.

        Args:
            document: Document to save.
            path: Target path; defaults to ``document.source_path``.

        Returns:
            The path written to.

        Raises:
            ValueError: If no path is available.
        """
        target = path or document.source_path
        if target is None:
            raise ValueError("No path specified for saving the config")
        target = Path(target)
        target.parent.mkdir(parents=True, exist_ok=True)
        yaml_text = ConfigService.to_yaml(document)
        target.write_text(yaml_text, encoding="utf-8")
        document.source_path = target
        document.mark_clean()
        return target

    @staticmethod
    def validate(document: ConfigDocument) -> Tuple[bool, str]:
        """Validate a document using organize's own config parser.

        Args:
            document: Document to validate.

        Returns:
            Tuple of ``(ok, message)``. On success message is empty or a
            confirmation string; on failure it describes the problem.
        """
        yaml_text = ConfigService.to_yaml(document)
        try:
            Config.from_string(
                config=yaml_text,
                config_path=document.source_path,
            )
            return True, "Configuration is valid."
        except ConfigError as exc:
            return False, str(exc)
        except Exception as exc:  # noqa: BLE001 — surface any parse error to UI
            return False, f"{type(exc).__name__}: {exc}"

    @staticmethod
    def default_config_dir() -> Path:
        """Return the preferred directory for organize configs."""
        from organize.find_config import USER_CONFIG_DIR, XDG_CONFIG_DIR

        if XDG_CONFIG_DIR.is_dir():
            return XDG_CONFIG_DIR
        return USER_CONFIG_DIR
