"""In-memory organize YAML document edited by the GUI."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from organize import Config
from organize.find_config import EXAMPLE_CONFIG

from ui.models.preset import Preset
from ui.models.preset_library import PresetLibrary
from ui.models.yaml_codec import YamlCodec


@dataclass
class ConfigDocument:
    """A config file (or unsaved buffer) the window is currently editing.

    ``text`` is the source of truth. The visual editor reads and writes
    the ``rules`` list; saving persists ``text`` to ``path``.
    """

    path: Optional[Path] = None
    text: str = field(default_factory=lambda: PresetLibrary().default().yaml)
    dirty: bool = False
    _codec: YamlCodec = field(default_factory=YamlCodec, repr=False, compare=False)

    @classmethod
    def blank(cls, preset: Optional[Preset] = None) -> "ConfigDocument":
        """Create an unsaved document from a preset (or the blank one)."""
        chosen = preset or PresetLibrary().default()
        return cls(path=None, text=chosen.yaml.lstrip("\n"), dirty=False)

    @classmethod
    def from_path(cls, path: Path) -> "ConfigDocument":
        """Load a document from disk."""
        return cls(path=path, text=path.read_text(encoding="utf-8"), dirty=False)

    @classmethod
    def example(cls) -> "ConfigDocument":
        """Load organize's shipped example config string."""
        return cls(path=None, text=EXAMPLE_CONFIG, dirty=False)

    @property
    def display_name(self) -> str:
        """File name shown in the title bar."""
        if self.path is None:
            return "Untitled"
        return self.path.name

    @property
    def display_path(self) -> str:
        """Full path or a placeholder for unsaved buffers."""
        if self.path is None:
            return "Unsaved config"
        return str(self.path)

    def data(self) -> Dict[str, Any]:
        """Parse YAML and require a mapping."""
        loaded = self._codec.loads(self.text)
        if not isinstance(loaded, dict):
            raise ValueError("Config must be a mapping with a top-level 'rules' key")
        return loaded

    def rules(self) -> List[Dict[str, Any]]:
        """Return the ``rules`` list, wrapping non-dict items."""
        rules = self.data().get("rules") or []
        if not isinstance(rules, list):
            raise ValueError("'rules' must be a list")
        return [rule if isinstance(rule, dict) else {"raw": rule} for rule in rules]

    def set_rules(self, rules: List[Dict[str, Any]]) -> None:
        """Replace ``rules`` and mark the document dirty."""
        try:
            data = self.data()
        except ValueError:
            data = {}
        data["rules"] = rules
        self.text = self._codec.dumps(data)
        self.dirty = True

    def validate(self) -> Config:
        """Parse the document with organize's real Config loader."""
        return Config.from_string(config=self.text, config_path=self.path)

    def save(self, path: Optional[Path] = None) -> Path:
        """Write ``text`` to ``path`` (or the existing path)."""
        target = path or self.path
        if target is None:
            raise ValueError("No path to save to")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(self.text, encoding="utf-8")
        self.path = target
        self.dirty = False
        return target

    def mark_text(self, text: str) -> None:
        """Update YAML text and set the dirty flag when it actually changed."""
        if text != self.text:
            self.text = text
            self.dirty = True
