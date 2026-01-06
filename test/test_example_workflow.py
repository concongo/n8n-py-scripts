"""
Tests for example_project/example_workflow
"""

import json
from pathlib import Path

import pytest

from src.example_project.example_workflow.step1_data_processing import process
from src.example_project.example_workflow.step2_analysis import analyze


@pytest.fixture
def fixtures_dir():
    """Get the fixtures directory for this workflow."""
    return (
        Path(__file__).parent
        / "fixtures"
        / "example_project"
        / "example_workflow"
    )


@pytest.fixture
def step1_input(fixtures_dir):
    """Load step1 input fixture."""
    with open(fixtures_dir / "step1_input.json") as f:
        return json.load(f)


@pytest.fixture
def step1_expected_output(fixtures_dir):
    """Load step1 expected output fixture."""
    with open(fixtures_dir / "step1_expected_output.json") as f:
        return json.load(f)


class TestStep1DataProcessing:
    """Tests for step1_data_processing."""

    def test_process_success(self, step1_input, step1_expected_output):
        """Test successful processing of input data."""
        result = process(step1_input)

        assert result["status"] == "success"
        assert result["row_count"] == step1_expected_output["row_count"]
        assert result["columns"] == step1_expected_output["columns"]

    def test_process_empty_items(self):
        """Test processing with no items."""
        result = process({"items": []})

        assert result["status"] == "error"
        assert "No items found" in result["message"]

    def test_process_no_items_key(self):
        """Test processing with missing items key."""
        result = process({})

        assert result["status"] == "error"


class TestStep2Analysis:
    """Tests for step2_analysis."""

    def test_analyze_success(self, step1_input):
        """Test analysis of successful processing."""
        # First process the data
        processed = process(step1_input)

        # Then analyze it
        result = analyze(processed)

        assert result["status"] == "success"
        assert result["analysis"]["total_rows"] == 3
        assert result["analysis"]["is_empty"] is False
        assert result["analysis"]["category"] == "small"

    def test_analyze_failed_previous_step(self):
        """Test analysis when previous step failed."""
        failed_data = {"status": "error", "message": "Previous error"}
        result = analyze(failed_data)

        assert result["status"] == "error"
        assert "Previous step failed" in result["message"]
