import importlib.util
import json
from pathlib import Path
from test.utils import with_n8n_items

import pytest


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
    return [{"json": enrich_raw_data_with_sector_names_output[0]}]


@pytest.fixture
def extract_filename_module():
    """Load the extract-filename module from its file path."""
    module_path = (
        Path(__file__).parents[1]
        / "src"
        / "portfolio_analysis"
        / "upload_position_file"
        / "extract_filename.py"
    )
    spec = importlib.util.spec_from_file_location(
        "extract_filename", module_path
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def cleanup_raw_data_for_storage_module():
    """Load the extract-filename module from its file path."""
    module_path = (
        Path(__file__).parents[1]
        / "src"
        / "portfolio_analysis"
        / "upload_position_file"
        / "cleanup_raw_data_for_storage.py"
    )
    spec = importlib.util.spec_from_file_location(
        "cleanup_raw_data_for_storage", module_path
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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
    def cleanup_raw_data_for_storage(
        self, request, cleanup_raw_data_for_storage_module
    ):
        result = extract_filename_module.cleanup_raw_data_for_storage()
        assert result
