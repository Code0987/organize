"""Load and save organize YAML configuration files."""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple

import yaml

from ui.models.config_document import ConfigDocument


class ConfigIOError(Exception):
    """Raised when a config file cannot be loaded or saved."""


def load_config(path: Path) -> ConfigDocument:
    """Load a config document from *path*.

    Raises:
        ConfigIOError: If the file is missing, unreadable, or invalid YAML.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ConfigIOError(f"Could not read {path}: {exc}") from exc

    try:
        raw = yaml.safe_load(text) or {}
    except yaml.YAMLError as exc:
        raise ConfigIOError(f"Invalid YAML in {path}: {exc}") from exc

    if not isinstance(raw, dict):
        raise ConfigIOError("Config root must be a mapping with a 'rules' key.")

    try:
        return ConfigDocument.from_config_dict(raw, path=path)
    except Exception as exc:  # noqa: BLE001 - surface parse issues to UI
        raise ConfigIOError(f"Could not parse config: {exc}") from exc


def save_config(document: ConfigDocument, path: Optional[Path] = None) -> Path:
    """Write *document* to YAML.

    Args:
        document: Config to save.
        path: Destination path; defaults to ``document.path``.

    Returns:
        The path written.

    Raises:
        ConfigIOError: If no path is available or writing fails.
    """
    target = path or document.path
    if target is None:
        raise ConfigIOError("No path specified for saving the config.")

    payload = document.to_config_dict()
    try:
        text = yaml.safe_dump(
            payload,
            sort_keys=False,
            allow_unicode=True,
            default_flow_style=False,
        )
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
    except OSError as exc:
        raise ConfigIOError(f"Could not write {target}: {exc}") from exc

    document.path = target
    document.mark_clean()
    return target


def document_to_yaml(document: ConfigDocument) -> str:
    """Return the YAML representation of *document* as a string."""
    return yaml.safe_dump(
        document.to_config_dict(),
        sort_keys=False,
        allow_unicode=True,
        default_flow_style=False,
    )


def validate_with_organize(document: ConfigDocument) -> Tuple[bool, str]:
    """Validate the document using organize's own config parser.

    Returns:
        ``(ok, message)`` where *message* is empty on success.
    """
    from organize import Config, ConfigError

    yaml_text = document_to_yaml(document)
    try:
        Config.from_string(yaml_text, config_path=document.path)
    except ConfigError as exc:
        return False, str(exc)
    except Exception as exc:  # noqa: BLE001
        return False, str(exc)
    return True, ""
