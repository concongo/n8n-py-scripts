import json
from datetime import date, datetime
from pathlib import Path
from test.utils import load_module, with_n8n_items

import pytest

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


@pytest.fixture
def fixtures_dir():
    """Get the fixtures directory for this workflow."""
    return (
        Path(__file__).parent
        / "fixtures"
        / "portfolio_analysis"
        / "upload_position_file"
    )


@pytest.fixture
def download_file_step_output(fixtures_dir):
    """Load step1 input fixture."""
    with open(fixtures_dir / "download_file_step.json") as f:
        return json.load(f)


@pytest.fixture
def enrich_raw_data_with_sector_names_output(fixtures_dir):
    """Load step1 input fixture."""
    with open(
        fixtures_dir / "enrich_raw_data_with_sector_names_output.json"
    ) as f:
        return json.load(f)


@pytest.fixture
def n8n_items(download_file_step_output):
    """Wrap fixture data using n8n's item shape."""
    return [{"json": download_file_step_output[0]}]


@pytest.fixture
def cleanup_raw_data_for_storage_input(
    enrich_raw_data_with_sector_names_output,
):
    """Wrap fixture data using n8n's item shape."""

    return [
        {"json": item} for item in enrich_raw_data_with_sector_names_output
    ]


@pytest.fixture
def clean_raw_data_for_storage(fixtures_dir):
    """Wrap fixture data using n8n's item shape."""

    with open(fixtures_dir / "clean_raw_data_for_storage.json") as f:
        return [{"json": json.load(f)}]


@pytest.fixture
def clean_raw_data_for_storage_output(fixtures_dir):
    """Wrap fixture data using n8n's item shape."""

    with open(fixtures_dir / "clean_and_prepare_fields.json") as f:
        return [{"json": row} for row in json.load(f)]


@pytest.fixture
def extract_filename_module():
    """Load the extract-filename module."""
    return load_module(
        "extract_filename",
        src_relative_path="portfolio_analysis/upload_position_file",
        test_file=Path(__file__),
    )


@pytest.fixture
def cleanup_raw_data_for_storage_module():
    """Load the cleanup_raw_data_for_storage module."""
    return load_module(
        "cleanup_raw_data_for_storage",
        src_relative_path="portfolio_analysis/upload_position_file",
        test_file=Path(__file__),
    )


@pytest.fixture
def calculate_security_type_aggregation_module():
    """Load the cleanup_raw_data_for_storage module."""
    return load_module(
        "calculate_security_type_aggregation",
        src_relative_path="portfolio_analysis/upload_position_file",
        test_file=Path(__file__),
    )


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
