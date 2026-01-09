"""Tests for the upload_position_file workflow."""

import json
from datetime import date, datetime

from test.utils import with_n8n_items

JSON_KEY = "json"


def date_serializer(obj):
    """Serialize date and datetime objects to ISO format strings."""
    if isinstance(obj, datetime):
        # Format datetime with space instead of 'T' to match expected format
        return obj.isoformat().replace("T", " ")
    if isinstance(obj, date):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


def remove_dynamic_timestamps(data):
    """Remove dynamic timestamp fields from nested data structures."""
    if isinstance(data, dict):
        return {
            k: remove_dynamic_timestamps(v)
            for k, v in data.items()
            if k not in ("updated_at", "imported_at")
        }
    elif isinstance(data, list):
        return [remove_dynamic_timestamps(item) for item in data]
    return data


class TestStep:
    @with_n8n_items(
        module_fixture_name="extract_filename_module",
        items_fixture_name="n8n_items",
    )
    def test_process_success(self, request, extract_filename_module):
        """Test extract_filename uses the injected _items global."""
        result = extract_filename_module.extract_filename()

        assert result["filename"].endswith(".csv")

    @with_n8n_items(
        module_fixture_name="cleanup_raw_data_for_storage_module",
        items_fixture_name="cleanup_raw_data_for_storage_input",
    )
    def test_cleanup_raw_data_for_storage(
        self,
        request,
        cleanup_raw_data_for_storage_module,
        clean_raw_data_for_storage,
    ):
        result = (
            cleanup_raw_data_for_storage_module.cleanup_raw_data_for_storage()
        )
        expected = clean_raw_data_for_storage[0]["json"]

        # Remove dynamic timestamps before comparison
        result_clean = remove_dynamic_timestamps(result)
        expected_clean = remove_dynamic_timestamps(expected)

        result_json = json.dumps(
            result_clean, default=date_serializer, sort_keys=True
        )
        expected_json = json.dumps(expected_clean, sort_keys=True)

        assert result_json == expected_json

    @with_n8n_items(
        module_fixture_name="calculate_security_type_aggregation_module",
        items_fixture_name="clean_raw_data_for_storage_output",
    )
    def test_calculate_security_type_aggregation(
        self,
        request,
        calculate_security_type_aggregation_module,
    ):
        result = calculate_security_type_aggregation_module.main()
        expected_result = {
            "snapshot_at": "2025-12-14 15:53:19+01:00",
            "mv__cash_and_money_market": 898.11,
            "mv__equity": 44479.98,
            "mv__fixed_income": 31967.82,
            "mv__total": 77345.91,
            "alloc__cash_and_money_market": 0.011611602992323704,
            "alloc__equity": 0.5750786305313365,
            "alloc__fixed_income": 0.4133097664763398,
        }
        assert result[0]["json"] == expected_result
