"""Position drift analysis comparing today vs yesterday snapshots.

This module analyzes position changes between consecutive trading days to
identify meaningful weight shifts, new/closed positions, and generate
rebalancing candidates.

Overview
--------
The analysis compares two portfolio snapshots (today and yesterday) to produce:

1. **Drift Metrics** - Which positions moved significantly in weight
2. **New/Closed Positions** - Positions that were added or removed
3. **Action Candidates** - Positions flagged for trim, add, replace, or review

Input Requirements
------------------
Each position row should contain:
- symbol: Stock ticker (e.g., "AAPL")
- sector: GICS sector classification
- rating: Quality rating from A (best) to F (worst)
- today_weight: Current position weight as decimal
- yesterday_weight: Previous day position weight as decimal
- delta_weight: Change in weight (today - yesterday)
- today_mv / yesterday_mv: Market values
- today_gain_pct: Unrealized gain/loss as decimal
- today_pe_ratio: Price-to-earnings ratio
- today_price_low_52w_ratio: Current price / 52-week low
- new_position / closed_position: Boolean flags

Output Metrics
--------------
The analysis produces:
- biggest_increase/decrease: Top movers by delta weight
- new_positions/closed_positions: Entry/exit activity
- candidates_trim/add/replace/review: Action recommendations

Usage
-----
Called from n8n workflow with position comparison data:

    result = main(items)  # items = [{"json": position_row}, ...]
    # Returns: [{"json": analysis_output}]
"""

from typing import Any

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
THRESHOLDS = {
    "min_abs_delta_weight": 0.001,  # 0.10% of account
    "big_move_abs_delta_weight": 0.005,  # 0.50%
    "trim_if_weight_above": 0.05,  # 5% position size
    "trim_if_gain_pct_above": 0.15,  # +15% gain
    "trim_if_pe_above": 45,  # stretched PE
    "add_if_weight_below": 0.03,  # underweight <3%
    "add_if_near_52w_low": 0.70,  # ratio <= 0.70
    "add_if_down_today": 0.0,  # day_change_pct < 0 implies down
    "replace_if_bad_rating_weight_min": 0.02,  # D/F and >=2%
    "review_if_missing_enrichment": True,
}

BAD_RATINGS = {"D", "F"}
GOOD_RATINGS = {"A", "B", "C"}
ENRICHMENT_KEYS = [
    "today_pe_ratio",
    "today_price_low_52w_ratio",
    "today_gain_pct",
]


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


def _get_rating(row: dict[str, Any]) -> str:
    """Extract and normalize rating from row."""
    return (row.get("rating") or "Unknown").strip()


def _is_enrichment_missing(row: dict[str, Any]) -> bool:
    """Check if key enrichment fields are missing."""
    return all(row.get(k) is None for k in ENRICHMENT_KEYS)


# ---------------------------------------------------------------------------
# Position Building
# ---------------------------------------------------------------------------
def _build_position(row: dict[str, Any]) -> dict[str, Any]:
    """Build normalized position dict from raw row data."""
    rating = _get_rating(row)
    enrichment_missing = _is_enrichment_missing(row)
    low_confidence = rating in BAD_RATINGS and enrichment_missing

    # Preserve original mv values (may be int or float from source)
    today_mv = row.get("today_mv")
    yesterday_mv = row.get("yesterday_mv")
    delta_mv = row.get("delta_mv")

    return {
        "symbol": row.get("symbol"),
        "sector": row.get("sector"),
        "rating": rating,
        "direction": row.get("direction"),
        "today_date": row.get("today_date"),
        "yesterday_date": row.get("yesterday_date"),
        "today_weight": float(_to_float(row.get("today_weight"), 0.0) or 0.0),
        "yesterday_weight": float(
            _to_float(row.get("yesterday_weight"), 0.0) or 0.0
        ),
        "delta_weight": float(_to_float(row.get("delta_weight"), 0.0) or 0.0),
        "today_mv": today_mv if today_mv is not None else 0.0,
        "yesterday_mv": yesterday_mv if yesterday_mv is not None else 0.0,
        "delta_mv": delta_mv if delta_mv is not None else 0.0,
        "today_qty": row.get("today_qty"),
        "yesterday_qty": row.get("yesterday_qty"),
        "today_price": _to_float(row.get("today_price"), None),
        "yesterday_price": _to_float(row.get("yesterday_price"), None),
        "today_gain_pct": _to_float(row.get("today_gain_pct"), None),
        "today_day_change_pct": _to_float(
            row.get("today_day_change_pct"), None
        ),
        "today_pe_ratio": _to_float(row.get("today_pe_ratio"), None),
        "today_price_low_52w_ratio": _to_float(
            row.get("today_price_low_52w_ratio"), None
        ),
        "new_position": bool(row.get("new_position")),
        "closed_position": bool(row.get("closed_position")),
        # Internal fields for candidate evaluation
        "_enrichment_missing": enrichment_missing,
        "_rating_low_confidence": low_confidence,
    }


# ---------------------------------------------------------------------------
# Candidate Evaluation
# ---------------------------------------------------------------------------
def _evaluate_trim_reasons(pos: dict[str, Any]) -> list[str]:
    """Evaluate reasons to trim a position."""
    reasons: list[str] = []
    weight = pos["today_weight"]
    if weight < THRESHOLDS["trim_if_weight_above"]:
        return reasons

    gain_pct = pos["today_gain_pct"]
    threshold = THRESHOLDS["trim_if_gain_pct_above"]
    if gain_pct is not None and gain_pct >= threshold:
        reasons.append(
            f"High weight ({weight:.2%}) and strong gain ({gain_pct:.2%})"
        )

    pe_ratio = pos["today_pe_ratio"]
    if pe_ratio is not None and pe_ratio >= THRESHOLDS["trim_if_pe_above"]:
        reasons.append(
            f"High weight ({weight:.2%}) and stretched PE ({pe_ratio:.1f})"
        )

    return reasons


def _evaluate_add_reasons(pos: dict[str, Any]) -> list[str]:
    """Evaluate reasons to add to a position."""
    reasons: list[str] = []
    rating = pos["rating"]
    weight = pos["today_weight"]

    max_weight = THRESHOLDS["add_if_weight_below"]
    if rating not in GOOD_RATINGS or weight > max_weight:
        return reasons

    low52 = pos["today_price_low_52w_ratio"]
    if low52 is not None and low52 <= THRESHOLDS["add_if_near_52w_low"]:
        reasons.append(
            f"Underweight ({weight:.2%}) and near 52w low (ratio {low52:.2f})"
        )

    day_change = pos["today_day_change_pct"]
    if day_change is not None and day_change < THRESHOLDS["add_if_down_today"]:
        reasons.append(
            f"Underweight ({weight:.2%}) and down today ({day_change:.2%})"
        )

    return reasons


def _evaluate_replace_reasons(pos: dict[str, Any]) -> list[str]:
    """Evaluate reasons to replace a position (bad rating, high confidence)."""
    reasons: list[str] = []
    rating = pos["rating"]
    weight = pos["today_weight"]

    if rating not in BAD_RATINGS or pos["_rating_low_confidence"]:
        return reasons

    if weight >= THRESHOLDS["replace_if_bad_rating_weight_min"]:
        reasons.append(
            f"Bad rating ({rating}) with meaningful weight ({weight:.2%})"
        )

    return reasons


def _evaluate_review_reasons(pos: dict[str, Any]) -> list[str]:
    """Evaluate reasons to review (missing enrichment or low confidence)."""
    if not THRESHOLDS["review_if_missing_enrichment"]:
        return []

    if pos["_enrichment_missing"] or pos["_rating_low_confidence"]:
        return ["Missing key enrichment fields; treat signals with caution."]

    return []


# ---------------------------------------------------------------------------
# Candidate Generation
# ---------------------------------------------------------------------------
def _make_candidate(pos: dict[str, Any], reasons: list[str]) -> dict[str, Any]:
    """Create a candidate dict from position and reasons."""
    return {
        "symbol": pos["symbol"],
        "sector": pos["sector"],
        "rating": pos["rating"],
        "today_weight": pos["today_weight"],
        "delta_weight": pos["delta_weight"],
        "today_mv": pos["today_mv"],
        "today_gain_pct": pos["today_gain_pct"],
        "today_pe_ratio": pos["today_pe_ratio"],
        "today_price_low_52w_ratio": pos["today_price_low_52w_ratio"],
        "enrichment_missing": pos["_enrichment_missing"],
        "rating_low_confidence": pos["_rating_low_confidence"],
        "reasons": reasons,
    }


def _strip_internal_fields(pos: dict[str, Any]) -> dict[str, Any]:
    """Remove internal fields (prefixed with _) from position dict."""
    return {k: v for k, v in pos.items() if not k.startswith("_")}


def _generate_candidates(
    positions: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    """Generate all candidate lists from positions."""
    trim: list[dict[str, Any]] = []
    add: list[dict[str, Any]] = []
    replace: list[dict[str, Any]] = []
    review: list[dict[str, Any]] = []

    for pos in positions:
        if reasons := _evaluate_review_reasons(pos):
            review.append(_make_candidate(pos, reasons))
            continue

        if reasons := _evaluate_trim_reasons(pos):
            trim.append(_make_candidate(pos, reasons))
        if reasons := _evaluate_add_reasons(pos):
            add.append(_make_candidate(pos, reasons))
        if reasons := _evaluate_replace_reasons(pos):
            replace.append(_make_candidate(pos, reasons))

    return {"trim": trim, "add": add, "replace": replace, "review": review}


def _sort_and_limit_candidates(
    candidates: dict[str, list[dict[str, Any]]],
) -> dict[str, list[dict[str, Any]]]:
    """Sort candidates by priority and limit to top 10."""
    trim = sorted(
        candidates["trim"],
        key=lambda c: (c["today_weight"], c["today_gain_pct"] or 0),
        reverse=True,
    )[:10]
    add = sorted(
        candidates["add"],
        key=lambda c: (
            c["today_weight"],
            c.get("today_price_low_52w_ratio") or 9.9,
        ),
    )[:10]
    replace = sorted(
        candidates["replace"],
        key=lambda c: c["today_weight"],
        reverse=True,
    )[:10]
    review = sorted(
        candidates["review"],
        key=lambda c: c["today_weight"],
        reverse=True,
    )[:10]

    return {"trim": trim, "add": add, "replace": replace, "review": review}


# ---------------------------------------------------------------------------
# Movers Analysis
# ---------------------------------------------------------------------------
def _filter_movers(positions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Filter positions with meaningful weight changes."""
    return [
        p
        for p in positions
        if abs(p["delta_weight"]) >= THRESHOLDS["min_abs_delta_weight"]
    ]


def _get_biggest_movers(
    movers: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    """Get top movers by increase, decrease, and absolute change."""
    biggest_increase = sorted(
        movers, key=lambda x: x["delta_weight"], reverse=True
    )[:5]
    biggest_decrease = sorted(movers, key=lambda x: x["delta_weight"])[:5]
    biggest_abs_move = sorted(
        movers, key=lambda x: abs(x["delta_weight"]), reverse=True
    )[:10]

    return {
        "increase": [_strip_internal_fields(p) for p in biggest_increase],
        "decrease": [_strip_internal_fields(p) for p in biggest_decrease],
        "absolute": [_strip_internal_fields(p) for p in biggest_abs_move],
    }


# ---------------------------------------------------------------------------
# Flags
# ---------------------------------------------------------------------------
def _build_flags(
    positions: list[dict[str, Any]],
    movers: list[dict[str, Any]],
    new_positions: list[dict[str, Any]],
    closed_positions: list[dict[str, Any]],
) -> dict[str, bool]:
    """Build portfolio-level drift flags."""
    return {
        "has_big_mover": any(
            abs(p["delta_weight"]) >= THRESHOLDS["big_move_abs_delta_weight"]
            for p in positions
        ),
        "has_new_positions": len(new_positions) > 0,
        "has_closed_positions": len(closed_positions) > 0,
        "many_movers": len(movers) >= max(10, int(0.25 * len(positions))),
    }


# ---------------------------------------------------------------------------
# Date Extraction
# ---------------------------------------------------------------------------
def _extract_dates(
    positions: list[dict[str, Any]],
) -> tuple[str | None, str | None]:
    """Extract today and yesterday dates from positions."""
    dates = sorted(
        {p["today_date"] for p in positions if p.get("today_date")},
        reverse=True,
    )
    today_date = dates[0] if dates else None
    yesterday_date = (
        positions[0].get("yesterday_date") if positions else None
    )
    return today_date, yesterday_date


# ---------------------------------------------------------------------------
# Main Entry Point
# ---------------------------------------------------------------------------
def _process_positions(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Process position rows and generate drift analysis."""
    positions = [_build_position(r) for r in rows]

    today_date, yesterday_date = _extract_dates(positions)

    movers = _filter_movers(positions)
    biggest_movers = _get_biggest_movers(movers)

    new_positions = [p for p in positions if p["new_position"]]
    closed_positions = [p for p in positions if p["closed_position"]]

    flags = _build_flags(positions, movers, new_positions, closed_positions)

    candidates = _generate_candidates(positions)
    candidates = _sort_and_limit_candidates(candidates)

    return {
        "metric": "Position drift (today vs yesterday)",
        "today_date": today_date,
        "yesterday_date": yesterday_date,
        "thresholds_used": THRESHOLDS,
        "counts": {
            "positions": len(positions),
            "movers": len(movers),
            "new_positions": len(new_positions),
            "closed_positions": len(closed_positions),
        },
        "flags": flags,
        "biggest_increase": biggest_movers["increase"],
        "biggest_decrease": biggest_movers["decrease"],
        "biggest_abs_move": biggest_movers["absolute"],
        "new_positions": [_strip_internal_fields(p) for p in new_positions],
        "closed_positions": [_strip_internal_fields(p) for p in closed_positions],
        "candidates_trim": candidates["trim"],
        "candidates_add": candidates["add"],
        "candidates_replace": candidates["replace"],
        "candidates_review": candidates["review"],
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
                    "metric": "Position drift (today vs yesterday)",
                    "error": "No rows received",
                }
            }
        ]

    return [{"json": _process_positions(rows)}]
