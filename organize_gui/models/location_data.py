"""Data model for a single rule location."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union

# Keys owned by LocationData; anything else is preserved in ``extra``.
_KNOWN_LOCATION_KEYS = frozenset(
    {
        "path",
        "min_depth",
        "max_depth",
        "exclude_files",
        "exclude_dirs",
        "filter",
        "filter_dirs",
        "ignore_errors",
    }
)


@dataclass
class LocationData:
    """Editable representation of an organize location entry.

    Attributes:
        path: One or more filesystem paths (or templates) to search.
        min_depth: Minimum directory depth to include.
        max_depth: Maximum depth, ``"inherit"``, or ``None`` for unlimited.
        exclude_files: Glob patterns of files to exclude.
        exclude_dirs: Glob patterns of directories to exclude.
        filter_files: Optional glob patterns of files to include only.
        filter_dirs: Optional glob patterns of directories to include only.
        ignore_errors: Whether to ignore walk errors for this location.
        extra: Additional location keys (e.g. ``search``, system excludes)
            preserved for round-trip fidelity with advanced configs.
    """

    path: List[str] = field(default_factory=list)
    min_depth: int = 0
    max_depth: Union[str, int, None] = "inherit"
    exclude_files: List[str] = field(default_factory=list)
    exclude_dirs: List[str] = field(default_factory=list)
    filter_files: Optional[List[str]] = None
    filter_dirs: Optional[List[str]] = None
    ignore_errors: bool = False
    extra: Dict[str, Any] = field(default_factory=dict)

    def display_label(self) -> str:
        """Return a short label for list widgets."""
        if not self.path:
            return "(no path)"
        if len(self.path) == 1:
            return self.path[0]
        return f"{self.path[0]} (+{len(self.path) - 1})"

    def is_simple(self) -> bool:
        """Return True if only a single path with default options is set."""
        return (
            len(self.path) == 1
            and self.min_depth == 0
            and self.max_depth == "inherit"
            and not self.exclude_files
            and not self.exclude_dirs
            and self.filter_files is None
            and self.filter_dirs is None
            and not self.ignore_errors
            and not self.extra
        )

    def to_yaml_value(self) -> Any:
        """Serialize to a value suitable for YAML dumping.

        Empty paths are serialized as ``{"path": ""}`` so callers never hit an
        ``IndexError``; organize validation will then report a clear error.
        """
        if self.is_simple():
            return self.path[0]

        if not self.path:
            path_val: Any = ""
        elif len(self.path) == 1:
            path_val = self.path[0]
        else:
            path_val = list(self.path)

        data: Dict[str, Any] = {"path": path_val}
        if self.min_depth != 0:
            data["min_depth"] = self.min_depth
        if self.max_depth != "inherit":
            data["max_depth"] = self.max_depth
        if self.exclude_files:
            data["exclude_files"] = list(self.exclude_files)
        if self.exclude_dirs:
            data["exclude_dirs"] = list(self.exclude_dirs)
        if self.filter_files is not None:
            data["filter"] = list(self.filter_files)
        if self.filter_dirs is not None:
            data["filter_dirs"] = list(self.filter_dirs)
        if self.ignore_errors:
            data["ignore_errors"] = self.ignore_errors
        # Preserve advanced / unknown keys for round-trip
        for key, value in self.extra.items():
            if key not in data:
                data[key] = value
        return data

    @classmethod
    def from_yaml_value(cls, value: Any) -> "LocationData":
        """Parse a YAML location value into a :class:`LocationData`."""
        if value is None:
            return cls()
        if isinstance(value, str):
            return cls(path=[value])
        if isinstance(value, list):
            paths = [str(v) for v in value]
            return cls(path=paths)
        if isinstance(value, dict):
            path_val = value.get("path", [])
            if isinstance(path_val, str):
                paths = [path_val]
            elif isinstance(path_val, list):
                paths = [str(p) for p in path_val]
            else:
                paths = [str(path_val)] if path_val else []
            filter_files = value.get("filter")
            if filter_files is not None and not isinstance(filter_files, list):
                filter_files = [str(filter_files)]
            filter_dirs = value.get("filter_dirs")
            if filter_dirs is not None and not isinstance(filter_dirs, list):
                filter_dirs = [str(filter_dirs)]
            exclude_files = value.get("exclude_files") or []
            if isinstance(exclude_files, str):
                exclude_files = [exclude_files]
            exclude_dirs = value.get("exclude_dirs") or []
            if isinstance(exclude_dirs, str):
                exclude_dirs = [exclude_dirs]
            extra = {
                key: val
                for key, val in value.items()
                if key not in _KNOWN_LOCATION_KEYS
            }
            return cls(
                path=paths,
                min_depth=int(value.get("min_depth", 0) or 0),
                max_depth=value.get("max_depth", "inherit"),
                exclude_files=list(exclude_files),
                exclude_dirs=list(exclude_dirs),
                filter_files=list(filter_files) if filter_files is not None else None,
                filter_dirs=list(filter_dirs) if filter_dirs is not None else None,
                ignore_errors=bool(value.get("ignore_errors", False)),
                extra=extra,
            )
        return cls(path=[str(value)])
