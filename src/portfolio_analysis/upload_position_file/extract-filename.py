"""
Extract the original filename from the first n8n item.
"""

from typing import Any


def extract_filename(items: list[dict[str, Any]] | None = None) -> dict[str, str]:
    """Return the filename from the first n8n item.

    Args:
        items: List of n8n items containing json data with originalFilename.
               If None, attempts to use global _items (legacy behavior).

    Returns:
        Dictionary with 'filename' key containing the original filename.

    Raises:
        NameError: If items is None and _items is not defined.
        ValueError: If items list is empty.
        KeyError: If item is missing json.originalFilename field.
    """
    if items is None:
        try:
            items = _items  # type: ignore[name-defined]
        except NameError as exc:
            raise NameError("_items is not defined") from exc

    if not items:
        raise ValueError("No items provided")

    first_item = items[0]
    try:
        return {"filename": first_item["json"]["originalFilename"]}
    except KeyError as exc:
        raise KeyError("Missing json.originalFilename in item") from exc
