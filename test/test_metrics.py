"""Tests for the upload_position_file workflow."""

from test.utils import with_n8n_items


class Test:
    @with_n8n_items(
        module_fixture_name="calculate_position_drift_module",
        items_fixture_name="position_drift_input",
    )
    def test_calculate_position_drift(
        self, request, calculate_position_drift_module, position_drift_output
    ):
        """Test extract_filename uses the injected _items global."""
        result = calculate_position_drift_module.main()
        assert result[0]["json"] == position_drift_output

    @with_n8n_items(
        module_fixture_name="calculate_sector_drift_module",
        items_fixture_name="sector_drift_input",
    )
    def test_calculate_sector_drift(
        self, request, calculate_sector_drift_module, sector_drift_output
    ):
        """Test extract_filename uses the injected _items global."""
        result = calculate_sector_drift_module.main()
        assert result[0]["json"] == sector_drift_output

    @with_n8n_items(
        module_fixture_name="calculate_position_drift_vs_yesterday_module",
        items_fixture_name="position_drift_vs_yesterday_input",
    )
    def test_calculate_position_drift_vs_yesterday(
        self,
        request,
        calculate_position_drift_vs_yesterday_module,
        position_drift_vs_yesterday_output,
    ):
        """Test extract_filename uses the injected _items global."""
        result = calculate_position_drift_vs_yesterday_module.main()
        assert result[0]["json"] == position_drift_vs_yesterday_output
