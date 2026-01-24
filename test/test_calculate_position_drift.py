"""Tests for the upload_position_file workflow."""

from test.utils import with_n8n_items

JSON_KEY = "json"


class TestStep:
    @with_n8n_items(
        module_fixture_name="calculate_position_drift_module",
        items_fixture_name="position_drift_input",
    )
    def test_process_success(
        self, request, calculate_position_drift_module, position_drift_output
    ):
        """Test extract_filename uses the injected _items global."""
        result = calculate_position_drift_module.main()
        assert result[0]["json"] == position_drift_output
