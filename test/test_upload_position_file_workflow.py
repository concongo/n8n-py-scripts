import importlib.util
import json
from pathlib import Path

import pytest


@pytest.fixture
def fixtures_dir():
    """Get the fixtures directory for this workflow."""
    return Path(__file__).parent / "fixtures" / "portfolio_analysis" / "upload_position_file"


@pytest.fixture
def download_file_step_output(fixtures_dir):
    """Load step1 input fixture."""
    with open(fixtures_dir / "download_file_step.json") as f:
        return json.load(f)


@pytest.fixture
def n8n_items(download_file_step_output):
    """Wrap fixture data using n8n's item shape."""
    return [{"json": download_file_step_output[0]}]


@pytest.fixture
def extract_filename_module():
    """Load the extract-filename module from its file path."""
    module_path = (
        Path(__file__).parents[1]
        / "src"
        / "portfolio_analysis"
        / "upload_position_file"
        / "extract-filename.py"
    )
    spec = importlib.util.spec_from_file_location("extract_filename", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestStep:
    def test_process_success(self, extract_filename_module, n8n_items):
        """Test extract_filename uses the injected _items global."""
        extract_filename_module._items = n8n_items

        result = extract_filename_module.extract_filename()

        assert result["filename"].endswith(".csv")
