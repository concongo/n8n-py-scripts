"""Shared test fixtures organized by project and workflow.

This conftest.py provides fixtures for all test files. Fixtures are organized
following the directory structure in test/fixtures/:
  - test/fixtures/portfolio_analysis/upload_position_file/
  - test/fixtures/example_project/example_workflow/

To add fixtures for a new workflow, add a new section below following
the same pattern.
"""

import json
from pathlib import Path

import pytest

from test.utils import load_module

# =============================================================================
# Portfolio Analysis - upload_position_file workflow
# =============================================================================


@pytest.fixture
def upload_position_fixtures_dir():
    """Fixtures directory for upload_position_file workflow."""
    return (
        Path(__file__).parent
        / "fixtures"
        / "portfolio_analysis"
        / "upload_position_file"
    )


# For backward compatibility
@pytest.fixture
def fixtures_dir(upload_position_fixtures_dir):
    """Alias for upload_position_fixtures_dir."""
    return upload_position_fixtures_dir


@pytest.fixture
def download_file_step_output(upload_position_fixtures_dir):
    """Load download_file_step output fixture."""
    with open(upload_position_fixtures_dir / "download_file_step.json") as f:
        return json.load(f)


@pytest.fixture
def enrich_raw_data_with_sector_names_output(upload_position_fixtures_dir):
    """Load enrich_raw_data_with_sector_names output fixture."""
    with open(
        upload_position_fixtures_dir
        / "enrich_raw_data_with_sector_names_output.json"
    ) as f:
        return json.load(f)


@pytest.fixture
def enrich_raw_data_with_sector_names_output_format_changed(
    upload_position_fixtures_dir,
):
    """Load enrich_raw_data_with_sector_names output fixture."""
    with open(
        upload_position_fixtures_dir
        / "enrich_raw_data_with_sector_names_output_format_changed.json"
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
    """Input data for cleanup_raw_data_for_storage step."""
    return [
        {"json": item} for item in enrich_raw_data_with_sector_names_output
    ]


@pytest.fixture
def cleanup_raw_data_for_storage_input_changed(
    enrich_raw_data_with_sector_names_output_format_changed,
):
    """Input data for cleanup_raw_data_for_storage step."""
    return [
        {"json": item}
        for item in enrich_raw_data_with_sector_names_output_format_changed
    ]


@pytest.fixture
def clean_raw_data_for_storage(upload_position_fixtures_dir):
    """Load clean_raw_data_for_storage output fixture."""
    with open(
        upload_position_fixtures_dir / "clean_raw_data_for_storage.json"
    ) as f:
        return [{"json": json.load(f)}]


@pytest.fixture
def clean_raw_data_for_storage_output(upload_position_fixtures_dir):
    """Load clean_and_prepare_fields output fixture."""
    with open(
        upload_position_fixtures_dir / "clean_and_prepare_fields.json"
    ) as f:
        return [{"json": row} for row in json.load(f)]


@pytest.fixture
def flat_aggregation_output(upload_position_fixtures_dir):
    with open(
        upload_position_fixtures_dir / "flat_aggregation_output.json"
    ) as f:
        return [{"json": row} for row in json.load(f)]


@pytest.fixture
def calculate_security_type_aggregation_detailed_output(
    upload_position_fixtures_dir,
):
    """Load calculate_security_type_aggregation_detailed output fixture."""
    with open(
        upload_position_fixtures_dir
        / "calculate_security_type_aggregation_detailed_output.json"
    ) as f:
        return [{"json": row} for row in json.load(f)]


@pytest.fixture
def extract_filename_module():
    """Load extract_filename module."""
    return load_module(
        "extract_filename",
        src_relative_path="portfolio_analysis/upload_position_file",
        test_file=Path(__file__),
    )


@pytest.fixture
def cleanup_raw_data_for_storage_module():
    """Load cleanup_raw_data_for_storage module."""
    return load_module(
        "cleanup_raw_data_for_storage",
        src_relative_path="portfolio_analysis/upload_position_file",
        test_file=Path(__file__),
    )


@pytest.fixture
def calculate_security_type_aggregation_module():
    """Load calculate_security_type_aggregation module."""
    return load_module(
        "calculate_security_type_aggregation",
        src_relative_path="portfolio_analysis/upload_position_file",
        test_file=Path(__file__),
    )


@pytest.fixture
def calculate_security_type_by_sector_aggregation_module():
    """Load calculate_security_type_aggregation module."""
    return load_module(
        "calculate_security_type_aggregation_by_sector",
        src_relative_path="portfolio_analysis/upload_position_file",
        test_file=Path(__file__),
    )


@pytest.fixture
def calculate_security_type_aggregation_detailed_module():
    """Load calculate_security_type_aggregation_detailed module."""
    return load_module(
        "calculate_security_type_aggregation_detailed",
        src_relative_path="portfolio_analysis/upload_position_file",
        test_file=Path(__file__),
    )


@pytest.fixture
def flat_aggregation_module():
    return load_module(
        "flat_aggregation",
        src_relative_path="portfolio_analysis/upload_position_file",
        test_file=Path(__file__),
    )


# =============================================================================
# Add new workflow fixtures below
# Example:
# =============================================================================
# # Project Name - workflow_name
# # =============================================================================
#
# @pytest.fixture
# def workflow_name_fixtures_dir():
#     """Fixtures directory for workflow_name."""
#     return Path(__file__).parent / "fixtures" / "project_name" / "workflow_name"
# =============================================================================


# =============================================================================
# Portfolio Analysis - position_drift
# =============================================================================
@pytest.fixture
def calculate_position_drift_module():
    return load_module(
        "calculate_position_drift",
        src_relative_path="portfolio_analysis/metrics/position_drift",
        test_file=Path(__file__),
    )


@pytest.fixture
def position_drift_fixtures_dir():
    """Fixtures directory for upload_position_file workflow."""
    return (
        Path(__file__).parent
        / "fixtures"
        / "portfolio_analysis"
        / "metrics"
        / "position_drift"
    )


@pytest.fixture
def position_drift_input(
    position_drift_fixtures_dir,
):
    with open(position_drift_fixtures_dir / "input.json") as f:
        return [{"json": row} for row in json.load(f)]


@pytest.fixture
def position_drift_output(
    position_drift_fixtures_dir,
):
    with open(position_drift_fixtures_dir / "output.json") as f:
        return json.load(f)[0]


# =============================================================================
# Portfolio Analysis - sector_drift
# =============================================================================
@pytest.fixture
def calculate_sector_drift_module():
    return load_module(
        "calculate_sector_drift",
        src_relative_path="portfolio_analysis/metrics/sector_drift",
        test_file=Path(__file__),
    )


@pytest.fixture
def sector_drift_fixtures_dir():
    """Fixtures directory for upload_sector_file workflow."""
    return (
        Path(__file__).parent
        / "fixtures"
        / "portfolio_analysis"
        / "metrics"
        / "sector_drift"
    )


@pytest.fixture
def sector_drift_input(
    sector_drift_fixtures_dir,
):
    with open(sector_drift_fixtures_dir / "input.json") as f:
        return [{"json": row} for row in json.load(f)]


@pytest.fixture
def sector_drift_output(
    sector_drift_fixtures_dir,
):
    with open(sector_drift_fixtures_dir / "output.json") as f:
        return json.load(f)[0]
