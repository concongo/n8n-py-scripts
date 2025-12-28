"""
Extract the original filename from the first n8n item.
"""


def extract_filename(items=None):
    """Return the filename from the first n8n item."""
    if items is None:
        try:
            items = _items
        except NameError as exc:
            raise NameError("_items is not defined") from exc

    if not items:
        raise ValueError("No items provided")

    first_item = items[0]
    try:
        return {"filename": first_item["json"]["originalFilename"]}
    except KeyError as exc:
        raise KeyError("Missing json.originalFilename in item") from exc
