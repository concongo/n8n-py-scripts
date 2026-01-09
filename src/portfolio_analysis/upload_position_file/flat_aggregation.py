"""Flattens sector aggregation data with holdings into individual rows."""

from typing import Any


def main(items: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    """Transform nested sector/holdings data into flat rows.

    Args:
        items: List of portfolio items with sector aggregation data

    Returns:
        List of flattened holding records wrapped in {"json": record} format

    Raises:
        NameError: If items is None and _items global is not defined
    """
    if items is None:
        try:
            items = _items  # type: ignore[name-defined]
        except NameError as exc:
            raise NameError("_items is not defined") from exc

    if not items:
        return []

    flattened_holdings = []

    for item in items:
        document = _extract_document(item)
        snapshot_metadata = _extract_snapshot_metadata(document)
        sectors = document.get("sectors", {}) or {}

        for sector_slug, sector_data in sectors.items():
            sector_metadata = _extract_sector_metadata(
                sector_slug, sector_data
            )
            holdings = sector_data.get("holdings", []) or []

            for holding in holdings:
                flat_holding = _create_flat_holding(
                    holding, snapshot_metadata, sector_metadata
                )
                flattened_holdings.append(flat_holding)

    return [{"json": record} for record in flattened_holdings]


def _extract_document(item: dict[str, Any]) -> dict[str, Any]:
    """Extract document data from item, handling n8n wrapper format."""
    return item.get("json", item)


def _extract_snapshot_metadata(document: dict[str, Any]) -> dict[str, Any]:
    """Extract snapshot-level metadata from document."""
    return {
        "snapshot_at": document.get("snapshot_at"),
        "mv_equity_total": document.get("mv__equity_total", 0.0),
        "mv_account_total": document.get("mv__account_total", 0.0),
    }


def _extract_sector_metadata(
    sector_slug: str, sector_data: dict[str, Any]
) -> dict[str, Any]:
    """Extract sector-level metadata."""
    return {
        "sector_slug": sector_slug,
        "sector_name": sector_data.get("sector"),
        "sector_market_value": sector_data.get("market_value", 0.0),
        "sector_alloc_pct_of_equity": sector_data.get(
            "alloc_pct_of_equity", 0.0
        ),
        "sector_alloc_pct_of_account": sector_data.get(
            "alloc_pct_of_account", 0.0
        ),
    }


def _create_flat_holding(
    holding: dict[str, Any],
    snapshot_metadata: dict[str, Any],
    sector_metadata: dict[str, Any],
) -> dict[str, Any]:
    """Create a flat holding record combining all metadata."""
    return {
        "snapshot_at": snapshot_metadata["snapshot_at"],
        "sector_slug": sector_metadata["sector_slug"],
        "sector": sector_metadata["sector_name"],
        "symbol": holding.get("symbol"),
        "name": holding.get("name"),
        "market_value": holding.get("market_value", 0.0),
        "alloc_of_equity": holding.get("alloc_of_equity", 0.0),
        "alloc_of_sector": holding.get("alloc_of_sector", 0.0),
        "alloc_of_account": holding.get("alloc_of_account", 0.0),
        "sector_market_value": sector_metadata["sector_market_value"],
        "sector_alloc_pct_of_equity": sector_metadata[
            "sector_alloc_pct_of_equity"
        ],
        "sector_alloc_pct_of_account": sector_metadata[
            "sector_alloc_pct_of_account"
        ],
        "mv__equity_total": snapshot_metadata["mv_equity_total"],
        "mv__account_total": snapshot_metadata["mv_account_total"],
    }
