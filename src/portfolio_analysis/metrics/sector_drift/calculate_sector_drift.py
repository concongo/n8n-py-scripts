"""Sector drift and concentration analysis for portfolio sectors.

This module analyzes sector-level portfolio data to assess sector concentration
risk and identify potential imbalances in sector allocation.

Overview
--------
The analysis takes aggregated sector data (from MongoDB aggregate) and produces
a comprehensive report including:

1. **Concentration Metrics** - How much of the portfolio is in top sectors
2. **Sector Details** - Weight, market value, and symbol count per sector
3. **Flags** - Boolean alerts for concentration issues

Input Requirements
------------------
Each sector row should contain:
- _id or sector: Sector name (e.g., "Information Technology")
- sector_mv: Total market value of positions in this sector
- sector_weight: Sector weight as decimal (e.g., 0.20 = 20%)
- symbols: List of stock tickers in this sector
- avg_pe: Average P/E ratio of positions in this sector

Output Metrics
--------------
Sector Summary:
- sectors_count: Total number of sectors
- top_sector: Details of largest sector by weight
- top3_sectors: Details of 3 largest sectors by weight

Concentration Metrics:
- top1_weight: Weight of the largest sector
- top3_weight: Combined weight of 3 largest sectors
- avg_sector_weight: Average weight per sector

Flags (boolean alerts):
- sector_concentration_high: Top sector exceeds 30% of portfolio
- top3_sector_concentration_high: Top 3 sectors exceed 60% of portfolio
- sector_count_low: Portfolio has fewer than 6 sectors
- sector_overcrowded: Top sector has 5+ symbols and 20%+ weight

Thresholds
----------
All thresholds are configurable via the THRESHOLDS constant:
- sector_concentration_high: 0.30 (30%)
- top3_concentration_high: 0.60 (60%)
- sector_count_low: 6 (minimum sectors)
- overcrowded_symbols: 5 (minimum symbols for overcrowded)
- overcrowded_weight: 0.20 (20% minimum weight for overcrowded)

Usage
-----
Called from n8n workflow with sector data from MongoDB aggregate:

    result = main(items)  # items = [{"json": sector_row}, ...]
    # Returns: [{"json": analysis_output}]
"""

from typing import Any

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
THRESHOLDS = {
    "sector_concentration_high": 0.30,
    "top3_concentration_high": 0.60,
    "sector_count_low": 6,
    "overcrowded_symbols": 5,
    "overcrowded_weight": 0.20,
}


# ---------------------------------------------------------------------------
# Conversion Helpers
# ---------------------------------------------------------------------------
def _to_float(value: Any, default: float | None = 0.0) -> float | None:
    """Safely convert value to float."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


# ---------------------------------------------------------------------------
# Sector Building
# ---------------------------------------------------------------------------
def _build_sector(row: dict[str, Any]) -> dict[str, Any]:
    """Build normalized sector dict from raw row data."""
    symbols = row.get("symbols") or []
    return {
        "sector": row.get("_id") or row.get("sector"),
        "sector_mv": _to_float(row.get("sector_mv")),
        "sector_weight": _to_float(row.get("sector_weight")),
        "symbols": symbols,
        "symbols_count": len(symbols),
        "avg_pe": _to_float(row.get("avg_pe"), None),
    }


def _build_sector_summary(sector: dict[str, Any]) -> dict[str, Any]:
    """Build sector summary dict for output (excludes symbols list)."""
    return {
        "sector": sector["sector"],
        "sector_weight": sector["sector_weight"],
        "sector_mv": sector["sector_mv"],
        "symbols_count": sector["symbols_count"],
        "avg_pe": sector["avg_pe"],
    }


# ---------------------------------------------------------------------------
# Concentration Calculations
# ---------------------------------------------------------------------------
def _calculate_concentration(
    sectors: list[dict[str, Any]],
) -> dict[str, float]:
    """Calculate concentration metrics from sorted sectors."""
    sectors_count = len(sectors)
    total_weight = sum(s["sector_weight"] for s in sectors)

    top1_weight = sectors[0]["sector_weight"] if sectors else 0.0
    top3_weight = sum(s["sector_weight"] for s in sectors[:3])
    avg_weight = total_weight / sectors_count if sectors_count else 0.0

    return {
        "top1_weight": top1_weight,
        "top3_weight": top3_weight,
        "avg_sector_weight": avg_weight,
    }


# ---------------------------------------------------------------------------
# Flag Evaluation
# ---------------------------------------------------------------------------
def _build_flags(
    top_sector: dict[str, Any],
    concentration: dict[str, float],
    sectors_count: int,
) -> dict[str, bool]:
    """Build analysis flags based on thresholds."""
    top1_weight = concentration["top1_weight"]
    top3_weight = concentration["top3_weight"]

    return {
        "sector_concentration_high": (
            top1_weight >= THRESHOLDS["sector_concentration_high"]
        ),
        "top3_sector_concentration_high": (
            top3_weight >= THRESHOLDS["top3_concentration_high"]
        ),
        "sector_count_low": sectors_count < THRESHOLDS["sector_count_low"],
        "sector_overcrowded": (
            top_sector["symbols_count"] >= THRESHOLDS["overcrowded_symbols"]
            and top1_weight >= THRESHOLDS["overcrowded_weight"]
        ),
    }


# ---------------------------------------------------------------------------
# Main Processing
# ---------------------------------------------------------------------------
def _process_sectors(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Process sector rows and generate drift analysis."""
    sectors = [_build_sector(r) for r in rows]
    sectors.sort(key=lambda x: x["sector_weight"], reverse=True)

    top_sector = sectors[0]
    top3_sectors = sectors[:3]
    concentration = _calculate_concentration(sectors)
    flags = _build_flags(top_sector, concentration, len(sectors))

    return {
        "metric": "Sector drift / concentration",
        "sectors_count": len(sectors),
        "top_sector": _build_sector_summary(top_sector),
        "top3_sectors": [_build_sector_summary(s) for s in top3_sectors],
        "concentration": concentration,
        "flags": flags,
        "all_sectors": sectors,
    }


# ---------------------------------------------------------------------------
# Main Entry Point
# ---------------------------------------------------------------------------
def main(items: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    """Main entry point for n8n integration."""
    if items is None:
        try:
            items = _items  # type: ignore[name-defined]
        except NameError as exc:
            raise NameError("_items is not defined") from exc

    rows = [it.get("json", {}) for it in items]

    if not rows:
        return [
            {
                "json": {
                    "metric": "Sector drift / concentration",
                    "error": "No sector data received from Mongo aggregate",
                }
            }
        ]

    return [{"json": _process_sectors(rows)}]
