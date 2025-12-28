"""
Example Step 1: Data Processing
This script demonstrates how to process input data from n8n.
"""

import pandas as pd


def process(data: dict) -> dict:
    """
    Process input data from n8n workflow.

    Args:
        data: Input dictionary containing the data from previous n8n step

    Returns:
        Dictionary with processed results
    """
    # Example: Extract items array from n8n input
    items = data.get("items", [])

    if not items:
        return {"status": "error", "message": "No items found"}

    # Convert to DataFrame for processing
    df = pd.DataFrame(items)

    # Example processing: calculate some statistics
    result = {
        "status": "success",
        "row_count": len(df),
        "columns": list(df.columns),
        "summary": df.describe().to_dict() if not df.empty else {},
    }

    return result
