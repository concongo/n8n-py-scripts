"""
Example Step 2: Data Analysis
This script demonstrates how to perform analysis on processed data.
"""


def analyze(data: dict) -> dict:
    """
    Analyze processed data from previous step.

    Args:
        data: Input dictionary containing processed data

    Returns:
        Dictionary with analysis results
    """
    if data.get("status") != "success":
        return {"status": "error", "message": "Previous step failed"}

    row_count = data.get("row_count", 0)

    # Example analysis
    result = {
        "status": "success",
        "analysis": {
            "total_rows": row_count,
            "is_empty": row_count == 0,
            "category": "small" if row_count < 100 else "large",
        },
    }

    return result
