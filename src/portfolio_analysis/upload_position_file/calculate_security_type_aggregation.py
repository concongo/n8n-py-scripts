"""Calculate security type aggregations from portfolio position data.

This module aggregates portfolio positions by security type and snapshot date,
computing both market values and allocation percentages. The output is in a
wide format with one row per snapshot date and columns for each security type.
"""

import re
from typing import Any

import pandas as pd

TOTAL_KEY = "--"


def slugify(col: str) -> str:
    """Convert a column name to a lowercase slug format.

    Normalizes column names by converting to lowercase, replacing special
    characters with underscores, and removing any invalid characters.

    Args:
        col: Column name to slugify

    Returns:
        Normalized column name (e.g., "Cash & Money Market" -> "cash_and_money_market")
    """
    s = (
        str(col)
        .strip()
        .lower()
        .replace("&", "and")
        .replace("/", "_")
        .replace("-", "_")
    )
    s = re.sub(r"\s+", "_", s)
    s = re.sub(r"[^a-z0-9_]", "", s)
    s = re.sub(r"_+", "_", s)
    return s.strip("_")


def prepare_dataframe(items: list[dict[str, Any]]) -> pd.DataFrame:
    """Convert n8n items to a DataFrame with normalized types.

    Args:
        items: List of n8n items with 'json' key containing position data

    Returns:
        DataFrame with normalized datetime and numeric columns

    Raises:
        ValueError: If 'snapshot_at' column is missing
    """
    rows = [it.get("json", it) for it in items]
    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)

    if "snapshot_at" not in df.columns:
        raise ValueError("Missing 'snapshot_at' in input items")

    df["snapshot_at"] = pd.to_datetime(df["snapshot_at"], errors="coerce")

    numeric_cols = [
        "market_value",
        "cost_basis",
        "gain_abs",
        "positions",
        "rows",
        "allocation_pct",
    ]
    for c in numeric_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    return df


def aggregate_by_security_type(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate data by snapshot date and security type.

    Args:
        df: DataFrame with position data

    Returns:
        Aggregated DataFrame with one row per (snapshot_at, security_type)
    """
    agg_map = {}
    for c in ["market_value", "cost_basis", "gain_abs"]:
        if c in df.columns:
            agg_map[c] = "sum"
    for c in ["positions", "rows"]:
        if c in df.columns:
            agg_map[c] = "sum"

    grouped = df.groupby(["snapshot_at", "security_type"], as_index=False).agg(
        agg_map
    )
    return grouped


def calculate_allocations(grouped: pd.DataFrame) -> pd.DataFrame:
    """Calculate allocation percentages for non-total security types.

    Args:
        grouped: Aggregated DataFrame with security types

    Returns:
        DataFrame with allocation_pct calculated for non-total rows

    Raises:
        ValueError: If 'market_value' column is missing
    """
    if "market_value" not in grouped.columns:
        raise ValueError("Missing 'market_value' in input items")

    totals = grouped[grouped["security_type"] == TOTAL_KEY].copy()
    non_totals = grouped[grouped["security_type"] != TOTAL_KEY].copy()

    denom = totals[["snapshot_at", "market_value"]].rename(
        columns={"market_value": "total_market_value"}
    )
    non_totals = non_totals.merge(denom, on="snapshot_at", how="left")

    fallback = non_totals.groupby("snapshot_at")["market_value"].transform(
        "sum"
    )
    non_totals["denom_mv"] = non_totals["total_market_value"].fillna(fallback)

    non_totals["allocation_pct"] = (
        non_totals["market_value"] / non_totals["denom_mv"]
    ).fillna(0.0)

    return non_totals


def pivot_to_wide_format(
    grouped: pd.DataFrame, non_totals: pd.DataFrame
) -> pd.DataFrame:
    """Pivot data to wide format with security types as columns.

    Args:
        grouped: Aggregated DataFrame with all security types (including totals)
        non_totals: DataFrame with non-total security types and allocations

    Returns:
        Wide-format DataFrame with mv__ and alloc__ prefixed columns
    """
    mv_for_pivot = grouped.copy()
    mv_for_pivot["security_type"] = mv_for_pivot["security_type"].replace(
        {TOTAL_KEY: "TOTAL"}
    )

    wide_mv = mv_for_pivot.pivot_table(
        index="snapshot_at",
        columns="security_type",
        values="market_value",
        aggfunc="sum",
        fill_value=0.0,
    ).reset_index()
    wide_mv.columns = ["snapshot_at"] + [
        f"mv__{slugify(c)}" for c in wide_mv.columns[1:]
    ]

    wide_alloc = non_totals.pivot_table(
        index="snapshot_at",
        columns="security_type",
        values="allocation_pct",
        aggfunc="sum",
        fill_value=0.0,
    ).reset_index()
    wide_alloc.columns = ["snapshot_at"] + [
        f"alloc__{slugify(c)}" for c in wide_alloc.columns[1:]
    ]

    wide = wide_mv.merge(wide_alloc, on="snapshot_at", how="left")
    wide["snapshot_at"] = wide["snapshot_at"].astype(str)
    wide = wide.fillna(0.0)

    return wide


def main(items: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    """Aggregate portfolio positions by security type and snapshot date.

    Takes n8n items with position data and returns aggregated data in wide format
    with one row per snapshot date. Market values include totals, allocations
    exclude totals.

    Args:
        items: List of n8n items containing position data. If None, uses global _items.

    Returns:
        List of n8n items with aggregated data in wide format

    Raises:
        NameError: If items is None and _items global is not defined
        ValueError: If required columns are missing from input data
    """
    if items is None:
        try:
            items = _items  # type: ignore[name-defined]
        except NameError as exc:
            raise NameError("_items is not defined") from exc

    if not items:
        return []

    df = prepare_dataframe(items)
    if df.empty:
        return []

    grouped = aggregate_by_security_type(df)
    non_totals = calculate_allocations(grouped)
    wide = pivot_to_wide_format(grouped, non_totals)

    out = wide.to_dict(orient="records")
    return [{"json": row} for row in out]
