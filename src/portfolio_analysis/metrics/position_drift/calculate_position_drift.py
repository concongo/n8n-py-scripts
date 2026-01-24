"""Position drift and concentration analysis for portfolio positions.

This module analyzes a portfolio snapshot to assess concentration risk, identify
positions that may need rebalancing, and generate actionable recommendations.

Overview
--------
The analysis takes enriched position data (with ratings, fundamentals, and price
metrics) and produces a comprehensive report including:

1. **Concentration Metrics** - How much of the portfolio is in the top positions
2. **Rating Distribution** - Allocation breakdown by quality rating (A-F)
3. **Action Candidates** - Positions flagged for trim, add, replace, or review

Input Requirements
------------------
Each position row should contain:
- symbol: Stock ticker (e.g., "AAPL")
- sector: GICS sector classification
- rating: Quality rating from A (best) to F (worst)
- alloc_of_account: Position weight as decimal (e.g., 0.05 = 5%)
- market_value: Current market value in dollars
- gain_pct: Unrealized gain/loss as decimal (e.g., 0.15 = 15% gain)
- gain_abs: Unrealized gain/loss in dollars
- pe_ratio: Price-to-earnings ratio
- price_low_52w_ratio: Current price / 52-week low (1.0 = at low, 2.0 = 100% above)
- snapshot_date: Date of the portfolio snapshot

Output Metrics
--------------
Portfolio Summary:
- all_positions_count: Total number of positions
- total_market_value: Sum of all position market values
- total_alloc_sum: Sum of weights (should be ~1.0 for complete portfolios)
- top5_weight: Combined weight of 5 largest positions
- top10_weight: Combined weight of 10 largest positions

Rating Analysis:
- rating_weight_breakdown: Dict mapping each rating to its total weight
- bad_rating_weight: Combined weight of D and F rated positions
- enrichment_missing_count: Positions lacking key fundamental data

Flags (boolean alerts):
- concentration_high: Top 10 positions exceed 45% of portfolio
- top5_high: Top 5 positions exceed 25% of portfolio
- bad_rating_weight_high: D/F rated positions exceed 20% of portfolio
- alloc_sum_not_one: Weights don't sum to ~100% (data quality issue)
- enrichment_missing_any: At least one position lacks enrichment data
- enrichment_missing_many: 15%+ of positions lack enrichment data

Action Candidates
-----------------
Each candidate list contains up to 10 positions with reasons for the action:

candidates_trim - Consider reducing position size:
- High weight (>=5%) with strong gains (>=15%)
- High weight (>=5%) with stretched P/E ratio (>=40)

candidates_add - Consider increasing position size:
- Good rating (A/B/C) + underweight (<=3%) + currently down
- Good rating (A/B/C) + underweight (<=3%) + near 52-week low (<=70% of low)

candidates_replace - Consider selling entirely:
- Bad rating (D/F) with meaningful weight (>=2%)
- Bad rating (D/F) and currently losing money

candidates_review_rating - Verify rating accuracy before acting:
- Bad rating (D/F) but missing enrichment data (low confidence in rating)

Thresholds
----------
All thresholds are configurable via the THRESHOLDS constant:
- top10_concentration_high: 0.45 (45%)
- top5_concentration_high: 0.25 (25%)
- trim_gain_pct: 0.15 (15% gain triggers trim consideration)
- trim_weight: 0.05 (5% minimum weight for trim)
- add_weight_max: 0.03 (3% maximum weight for add candidates)
- add_near_52w_low: 0.70 (70% of 52-week low)
- replace_weight_min: 0.02 (2% minimum weight for replace)
- bad_rating_weight_high: 0.20 (20% max for D/F rated positions)

Usage
-----
Called from n8n workflow with position data from MongoDB aggregate:

    result = main(items)  # items = [{"json": position_row}, ...]
    # Returns: [{"json": analysis_output}]

Note: This module avoids class definitions to ensure compatibility with n8n's
restricted Python sandbox environment.
"""

from typing import Any

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
THRESHOLDS = {
    "top10_concentration_high": 0.45,
    "top5_concentration_high": 0.25,
    "trim_gain_pct": 0.15,
    "trim_weight": 0.05,
    "add_weight_max": 0.03,
    "add_near_52w_low": 0.70,
    "replace_weight_min": 0.02,
    "bad_rating_weight_high": 0.20,
}

BAD_RATINGS = {"D", "F"}
GOOD_RATINGS = {"A", "B", "C"}
ENRICHMENT_KEYS = ["gain_pct", "pe_ratio", "price_low_52w_ratio"]


# ---------------------------------------------------------------------------
# Conversion Helpers
# ---------------------------------------------------------------------------
def _to_float(value: Any, default: float | None = 0.0) -> float | None:
    """Safely convert value to float."""
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _get_weight(row: dict[str, Any]) -> float:
    """Extract allocation weight from row."""
    return float(_to_float(row.get("alloc_of_account"), 0.0) or 0.0)


def _get_rating(row: dict[str, Any]) -> str:
    """Extract and normalize rating from row."""
    return (row.get("rating") or "Unknown").strip()


def _is_enrichment_missing(row: dict[str, Any]) -> bool:
    """Check if key enrichment fields are missing."""
    return all(row.get(k) in (None, "", "N/A") for k in ENRICHMENT_KEYS)


# ---------------------------------------------------------------------------
# Position Building
# ---------------------------------------------------------------------------
def _build_position(row: dict[str, Any]) -> dict[str, Any]:
    """Build normalized position dict from raw row data."""
    rating = _get_rating(row)
    enrichment_missing = _is_enrichment_missing(row)
    low_confidence = rating in BAD_RATINGS and enrichment_missing

    return {
        "symbol": row.get("symbol"),
        "sector": row.get("sector"),
        "rating": row.get("rating"),
        "alloc_of_account": _get_weight(row),
        "market_value": float(_to_float(row.get("market_value"), 0.0) or 0.0),
        "gain_pct": _to_float(row.get("gain_pct"), None),
        "gain_abs": _to_float(row.get("gain_abs"), None),
        "pe_ratio": _to_float(row.get("pe_ratio"), None),
        "price_low_52w_ratio": _to_float(row.get("price_low_52w_ratio"), None),
        "enrichment_missing": enrichment_missing,
        "rating_low_confidence": low_confidence,
    }


# ---------------------------------------------------------------------------
# Candidate Evaluation
# ---------------------------------------------------------------------------
def _evaluate_trim_reasons(pos: dict[str, Any]) -> list[str]:
    """Evaluate reasons to trim a position."""
    reasons = []
    w = pos["alloc_of_account"]
    if w < THRESHOLDS["trim_weight"]:
        return reasons

    gain_pct = pos["gain_pct"]
    if gain_pct is not None and gain_pct >= THRESHOLDS["trim_gain_pct"]:
        reasons.append(
            f"High weight ({w:.2%}) and strong gain ({gain_pct:.2%})"
        )

    pe_ratio = pos["pe_ratio"]
    if pe_ratio is not None and pe_ratio >= 40:
        reasons.append(f"High weight ({w:.2%}) and stretched PE ({pe_ratio:.2f})")

    return reasons


def _evaluate_add_reasons(pos: dict[str, Any]) -> list[str]:
    """Evaluate reasons to add to a position."""
    reasons = []
    rating = _get_rating({"rating": pos["rating"]})
    w = pos["alloc_of_account"]

    if rating not in GOOD_RATINGS or w > THRESHOLDS["add_weight_max"]:
        return reasons

    gain_pct = pos["gain_pct"]
    if gain_pct is not None and gain_pct < 0:
        reasons.append(
            f"Good rating ({rating}), underweight ({w:.2%}), down ({gain_pct:.2%})"
        )

    low52 = pos["price_low_52w_ratio"]
    if low52 is not None and low52 <= THRESHOLDS["add_near_52w_low"]:
        reasons.append(
            f"Good rating ({rating}), underweight ({w:.2%}), near 52w low (ratio {low52:.2f})"
        )

    return reasons


def _evaluate_replace_reasons(pos: dict[str, Any]) -> list[str]:
    """Evaluate reasons to replace a position (bad rating, high confidence)."""
    reasons = []
    rating = _get_rating({"rating": pos["rating"]})
    w = pos["alloc_of_account"]

    if rating not in BAD_RATINGS or pos["rating_low_confidence"]:
        return reasons

    if w >= THRESHOLDS["replace_weight_min"]:
        reasons.append(f"Bad rating ({rating}) with meaningful weight ({w:.2%})")

    gain_pct = pos["gain_pct"]
    if gain_pct is not None and gain_pct < 0:
        reasons.append(f"Bad rating ({rating}) and losing ({gain_pct:.2%})")

    return reasons


def _evaluate_review_reasons(pos: dict[str, Any]) -> list[str]:
    """Evaluate reasons to review rating (bad rating but low confidence)."""
    rating = _get_rating({"rating": pos["rating"]})
    if rating in BAD_RATINGS and pos["rating_low_confidence"]:
        return [
            "Bad rating but enrichment missing (low confidence). "
            "Verify rating inputs / fundamentals."
        ]
    return []


# ---------------------------------------------------------------------------
# Candidate Generation
# ---------------------------------------------------------------------------
def _make_candidate(pos: dict[str, Any], reasons: list[str]) -> dict[str, Any]:
    """Create a candidate dict from position and reasons."""
    return {**pos, "reasons": reasons}


def _generate_candidates(
    positions: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    """Generate all candidate lists from positions."""
    trim: list[dict[str, Any]] = []
    add: list[dict[str, Any]] = []
    replace: list[dict[str, Any]] = []
    review: list[dict[str, Any]] = []

    for pos in positions:
        if reasons := _evaluate_trim_reasons(pos):
            trim.append(_make_candidate(pos, reasons))
        if reasons := _evaluate_add_reasons(pos):
            add.append(_make_candidate(pos, reasons))
        if reasons := _evaluate_replace_reasons(pos):
            replace.append(_make_candidate(pos, reasons))
        if reasons := _evaluate_review_reasons(pos):
            review.append(_make_candidate(pos, reasons))

    return {"trim": trim, "add": add, "replace": replace, "review": review}


def _sort_and_limit_candidates(
    candidates: dict[str, list[dict[str, Any]]],
) -> dict[str, list[dict[str, Any]]]:
    """Sort candidates by priority and limit to top 10."""
    trim = sorted(
        candidates["trim"],
        key=lambda c: (c["alloc_of_account"], c["gain_pct"] or 0),
        reverse=True,
    )[:10]
    add = sorted(
        candidates["add"],
        key=lambda c: (c["alloc_of_account"], c["gain_pct"] or 0),
    )[:10]
    replace = sorted(
        candidates["replace"],
        key=lambda c: c["alloc_of_account"],
        reverse=True,
    )[:10]
    review = sorted(
        candidates["review"],
        key=lambda c: c["alloc_of_account"],
        reverse=True,
    )[:10]

    return {"trim": trim, "add": add, "replace": replace, "review": review}


# ---------------------------------------------------------------------------
# Aggregation / Summary
# ---------------------------------------------------------------------------
def _calculate_top_weight(rows: list[dict[str, Any]], n: int) -> float:
    """Calculate sum of top N position weights."""
    return float(sum(_get_weight(r) for r in rows[:n]))


def _calculate_rating_breakdown(
    rows: list[dict[str, Any]],
) -> tuple[dict[str, float], float, int]:
    """Calculate rating weight breakdown, bad weight, and enrichment missing count."""
    breakdown: dict[str, float] = {}
    bad_weight = 0.0
    missing_count = 0

    for row in rows:
        rating = _get_rating(row)
        weight = _get_weight(row)
        breakdown[rating] = breakdown.get(rating, 0.0) + weight

        if rating in BAD_RATINGS:
            bad_weight += weight
        if _is_enrichment_missing(row):
            missing_count += 1

    return breakdown, bad_weight, missing_count


def _build_flags(
    top5: float,
    top10: float,
    bad_weight: float,
    alloc_sum: float,
    missing_count: int,
    total_rows: int,
) -> dict[str, bool]:
    """Build analysis flags based on thresholds."""
    return {
        "concentration_high": top10 >= THRESHOLDS["top10_concentration_high"],
        "top5_high": top5 >= THRESHOLDS["top5_concentration_high"],
        "bad_rating_weight_high": bad_weight
        >= THRESHOLDS["bad_rating_weight_high"],
        "alloc_sum_not_one": abs(alloc_sum - 1.0) > 0.03,
        "enrichment_missing_any": missing_count > 0,
        "enrichment_missing_many": missing_count
        >= max(3, int(0.15 * total_rows)),
    }


# ---------------------------------------------------------------------------
# Main Entry Point
# ---------------------------------------------------------------------------
def _process_positions(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Process position rows and generate drift analysis."""
    rows.sort(key=lambda r: _get_weight(r), reverse=True)

    snapshot_date = rows[0].get("snapshot_date")
    total_market_value = float(
        sum(_to_float(r.get("market_value"), 0.0) or 0.0 for r in rows)
    )
    total_alloc_sum = float(sum(_get_weight(r) for r in rows))

    top5_weight = _calculate_top_weight(rows, 5)
    top10_weight = _calculate_top_weight(rows, 10)
    rating_breakdown, bad_weight, missing_count = _calculate_rating_breakdown(
        rows
    )

    positions = [_build_position(r) for r in rows]
    top3 = positions[:3]
    top15 = positions[:15]

    candidates = _generate_candidates(positions)
    candidates = _sort_and_limit_candidates(candidates)

    flags = _build_flags(
        top5_weight,
        top10_weight,
        bad_weight,
        total_alloc_sum,
        missing_count,
        len(rows),
    )

    return {
        "metric": "Position drift / concentration (latest snapshot)",
        "snapshot_date": snapshot_date,
        "all_positions_count": len(rows),
        "total_market_value": total_market_value,
        "total_alloc_sum": total_alloc_sum,
        "top5_weight": top5_weight,
        "top10_weight": top10_weight,
        "rating_weight_breakdown": rating_breakdown,
        "bad_rating_weight": bad_weight,
        "enrichment_missing_count": missing_count,
        "flags": flags,
        "thresholds_used": THRESHOLDS,
        "top3_positions": top3,
        "top_positions": top15,
        "candidates_trim": candidates["trim"],
        "candidates_add": candidates["add"],
        "candidates_replace": candidates["replace"],
        "candidates_review_rating": candidates["review"],
    }


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
                    "error": "No positions returned from Mongo aggregate.",
                    "metric": "Position drift / concentration (latest snapshot)",
                }
            }
        ]

    return [{"json": _process_positions(rows)}]
