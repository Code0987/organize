"""Tests for filter/action schema catalogues used by the form UI."""

from __future__ import annotations

from organize.actions import ALL as ALL_ACTIONS
from organize.filters import ALL as ALL_FILTERS
from organize_gui.models.action_schemas import ACTION_SCHEMAS, get_action_schema
from organize_gui.models.filter_schemas import FILTER_SCHEMAS, get_filter_schema
from organize_gui.models.item_schema import ItemSchema


class TestSchemaCoverage:
    def test_all_organize_filters_have_schemas(self) -> None:
        registry_names = {f.filter_config.name for f in ALL_FILTERS}
        schema_names = set(FILTER_SCHEMAS.keys())
        missing = registry_names - schema_names
        assert not missing, f"Filters missing GUI schemas: {missing}"

    def test_all_organize_actions_have_schemas(self) -> None:
        registry_names = {a.action_config.name for a in ALL_ACTIONS}
        schema_names = set(ACTION_SCHEMAS.keys())
        missing = registry_names - schema_names
        assert not missing, f"Actions missing GUI schemas: {missing}"

    def test_get_filter_schema_unknown_fallback(self) -> None:
        schema = get_filter_schema("totally_unknown_filter")
        assert isinstance(schema, ItemSchema)
        assert schema.name == "totally_unknown_filter"

    def test_get_action_schema_unknown_fallback(self) -> None:
        schema = get_action_schema("totally_unknown_action")
        assert schema.name == "totally_unknown_action"

    def test_default_params_keys_match_fields(self) -> None:
        for name, schema in FILTER_SCHEMAS.items():
            params = schema.default_params()
            for field in schema.fields:
                assert field.name in params, f"{name} missing default for {field.name}"

    def test_action_default_params_keys_match_fields(self) -> None:
        for name, schema in ACTION_SCHEMAS.items():
            params = schema.default_params()
            for field in schema.fields:
                assert field.name in params, f"{name} missing default for {field.name}"
