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
        module_fixture_name="cleanup_raw_data_for_storage_module",
        items_fixture_name="cleanup_raw_data_for_storage_input_changed",
    )
    def test_cleanup_raw_data_for_storage_new_format(
        self,
        request,
        cleanup_raw_data_for_storage_module,
    ):
        """Test cleanup with Excel formula format (="$value")."""
        result = (
            cleanup_raw_data_for_storage_module.cleanup_raw_data_for_storage()
        )

        # Verify we got results
        assert len(result) > 0

        # Find AAPL position to verify Excel formula parsing
        aapl = next(
            (r for r in result if r["asset"]["symbol"] == "AAPL"), None
        )
        assert aapl is not None

        # Verify Excel formula format was correctly parsed
        # Input: "=\"$259.939\"" should be parsed as 259.939
        assert aapl["position"]["price"] == 259.939

        # Verify negative value in Excel formula format
        # Input: "=\"-$0.311\"" should be parsed as -0.311
        assert aapl["position"]["price_change_abs"] == -0.311

        # Verify the source file is the new format
        assert "2026-01-13" in aapl["source_file_name"]

        # Verify basic structure is maintained
        assert "account_id" in aapl
        assert "asset_key" in aapl
        assert "position" in aapl
        assert "asset" in aapl

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

    @with_n8n_items(
        module_fixture_name=(
            "calculate_security_type_by_sector_aggregation_module"
        ),
        items_fixture_name="clean_raw_data_for_storage_output",
    )
    def test_calculate_security_type_by_sector_aggregation(
        self,
        request,
        calculate_security_type_by_sector_aggregation_module,
    ):
        result = calculate_security_type_by_sector_aggregation_module.main()
        expected_result = {
            "snapshot_at": "2025-12-14 15:53:19+01:00",
            "mv__communication_services": 309.29,
            "mv__consumer_discretionary": 2048.87,
            "mv__consumer_staples": 9339,
            "mv__energy": 908.82,
            "mv__health_care": 8380.89,
            "mv__industrials": 10667.71,
            "mv__information_technology": 8300.96,
            "mv__utilities": 3345.92,
            "alloc__communication_services": 0.0071427152802699964,
            "alloc__consumer_discretionary": 0.04731641843023306,
            "alloc__consumer_staples": 0.2156740211530974,
            "alloc__energy": 0.020988206864156544,
            "alloc__health_care": 0.19354751548793042,
            "alloc__industrials": 0.24635912969216278,
            "alloc__information_technology": 0.1917016192987488,
            "alloc__utilities": 0.07727037379340096,
            "mv__equity_total": 43301.46,
            "mv__account_total": 77345.91,
        }
        assert result[0]["json"] == expected_result

    @with_n8n_items(
        module_fixture_name=(
            "calculate_security_type_aggregation_detailed_module"
        ),
        items_fixture_name="clean_raw_data_for_storage_output",
    )
    def test_calculate_security_type_aggregation_detailed(
        self,
        request,
        calculate_security_type_aggregation_detailed_module,
        calculate_security_type_aggregation_detailed_output,
    ):
        result = calculate_security_type_aggregation_detailed_module.main()
        assert result == calculate_security_type_aggregation_detailed_output

    @with_n8n_items(
        module_fixture_name=("flat_aggregation_module"),
        items_fixture_name=(
            "calculate_security_type_aggregation_detailed_output"
        ),
    )
    def test_flat_aggregation(
        self,
        request,
        flat_aggregation_module,
        flat_aggregation_output,
    ):
        result = flat_aggregation_module.main()
        assert result == flat_aggregation_output
