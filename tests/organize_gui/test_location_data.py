"""Tests for LocationData serialization and parsing."""

from __future__ import annotations

import pytest

from organize_gui.models.location_data import LocationData


class TestLocationDataBasics:
    """Happy-path location model behaviour."""

    def test_from_string_path(self) -> None:
        loc = LocationData.from_yaml_value("~/Downloads")
        assert loc.path == ["~/Downloads"]
        assert loc.is_simple()
        assert loc.to_yaml_value() == "~/Downloads"

    def test_from_dict_with_options(self) -> None:
        loc = LocationData.from_yaml_value(
            {
                "path": "~/Downloads",
                "min_depth": 1,
                "max_depth": 3,
                "exclude_files": ["*.tmp"],
                "exclude_dirs": [".git"],
                "filter": ["*.pdf"],
                "filter_dirs": ["docs"],
                "ignore_errors": True,
            }
        )
        assert loc.path == ["~/Downloads"]
        assert loc.min_depth == 1
        assert loc.max_depth == 3
        assert loc.exclude_files == ["*.tmp"]
        assert loc.exclude_dirs == [".git"]
        assert loc.filter_files == ["*.pdf"]
        assert loc.filter_dirs == ["docs"]
        assert loc.ignore_errors is True
        assert not loc.is_simple()

    def test_multi_path_round_trip(self) -> None:
        loc = LocationData.from_yaml_value(
            {"path": ["~/Downloads", "~/Desktop"], "min_depth": 0}
        )
        assert loc.path == ["~/Downloads", "~/Desktop"]
        serialized = loc.to_yaml_value()
        assert isinstance(serialized, dict)
        assert serialized["path"] == ["~/Downloads", "~/Desktop"]
        again = LocationData.from_yaml_value(serialized)
        assert again.path == ["~/Downloads", "~/Desktop"]

    def test_display_label(self) -> None:
        assert LocationData(path=[]).display_label() == "(no path)"
        assert LocationData(path=["a"]).display_label() == "a"
        assert LocationData(path=["a", "b"]).display_label() == "a (+1)"

    def test_list_of_paths_parsed(self) -> None:
        loc = LocationData.from_yaml_value(["~/a", "~/b"])
        assert loc.path == ["~/a", "~/b"]


class TestLocationDataEmptyPath:
    """Desired behaviour for empty paths (review issue #1)."""

    def test_empty_path_to_yaml_does_not_raise(self) -> None:
        """Serializing an empty path must not raise IndexError.

        Empty locations are invalid for organize, but the editor must
        produce a clean error path rather than crashing mid-serialize.
        """
        loc = LocationData(path=[], min_depth=1)  # non-simple -> complex branch
        # Must not raise IndexError
        value = loc.to_yaml_value()
        assert value is not None

    def test_empty_path_simple_does_not_raise(self) -> None:
        loc = LocationData(path=[])
        # is_simple is False when path is empty (len != 1)
        assert not loc.is_simple()
        value = loc.to_yaml_value()
        assert value is not None


class TestLocationDataExtraFields:
    """Desired behaviour for advanced location fields (review issue #7)."""

    def test_preserves_search_and_system_excludes_on_round_trip(self) -> None:
        """Custom search / system_exclude_* must survive load → save."""
        raw = {
            "path": "~/Downloads",
            "search": "depth",
            "system_exclude_files": ["Thumbs.db"],
            "system_exclude_dirs": [".svn"],
        }
        loc = LocationData.from_yaml_value(raw)
        serialized = loc.to_yaml_value()
        assert isinstance(serialized, dict)
        assert serialized.get("search") == "depth"
        assert serialized.get("system_exclude_files") == ["Thumbs.db"]
        assert serialized.get("system_exclude_dirs") == [".svn"]
