import re
from typing import Any

import pandas as pd

TOTAL_KEY = "--"

# --- knobs you can tweak ---
DROP_UNKNOWN_SECTOR = True
EQUITY_ASSET_PREFIX = "EQUITY:"
# ---------------------------


def slugify(col: str) -> str:
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


def _validate_required_columns(df: pd.DataFrame) -> None:
    required_columns = ["snapshot_at", "market_value", "asset_key"]
    for col in required_columns:
        if col not in df.columns:
            raise ValueError(f"Missing '{col}' in input items")


def _normalize_snapshot_date(df: pd.DataFrame) -> pd.DataFrame:
    df["snapshot_at"] = pd.to_datetime(df["snapshot_at"], errors="coerce")
    return df


def _normalize_market_value(df: pd.DataFrame) -> pd.DataFrame:
    df["market_value"] = pd.to_numeric(
        df["market_value"], errors="coerce"
    ).fillna(0.0)
    return df


def _normalize_sector(df: pd.DataFrame) -> pd.DataFrame:
    if "sector" not in df.columns:
        df["sector"] = None
    df["sector"] = df["sector"].astype("object")
    df["sector"] = df["sector"].where(df["sector"].notna(), "")
    df["sector"] = df["sector"].astype(str).str.strip()
    return df


def _extract_account_total(df: pd.DataFrame) -> pd.DataFrame | None:
    if "security_type" not in df.columns:
        return None
    totals = df[df["security_type"] == TOTAL_KEY]
    if totals.empty:
        return None
    return totals.groupby("snapshot_at", as_index=False).agg(
        mv__account_total=("market_value", "sum")
    )


def _filter_equity_positions(df: pd.DataFrame) -> pd.DataFrame:
    df_positions = df.copy()
    if "security_type" in df_positions.columns:
        df_positions = df_positions[df_positions["security_type"] != TOTAL_KEY]

    df_equity = df_positions[
        df_positions["asset_key"]
        .astype(str)
        .str.startswith(EQUITY_ASSET_PREFIX)
    ].copy()

    if DROP_UNKNOWN_SECTOR:
        df_equity = df_equity[df_equity["sector"] != ""]

    df_equity.loc[df_equity["sector"] == "", "sector"] = "unknown"
    return df_equity


def _calculate_sector_aggregations(df_equity: pd.DataFrame) -> pd.DataFrame:
    sector_grouped = df_equity.groupby(
        ["snapshot_at", "sector"], as_index=False
    ).agg(market_value=("market_value", "sum"))

    equity_total = df_equity.groupby("snapshot_at", as_index=False).agg(
        mv__equity_total=("market_value", "sum")
    )

    sector_grouped = sector_grouped.merge(
        equity_total, on="snapshot_at", how="left"
    )
    sector_grouped["allocation_pct"] = (
        sector_grouped["market_value"] / sector_grouped["mv__equity_total"]
    ).fillna(0.0)

    return sector_grouped, equity_total


def _pivot_market_values(sector_grouped: pd.DataFrame) -> pd.DataFrame:
    wide_mv = sector_grouped.pivot_table(
        index="snapshot_at",
        columns="sector",
        values="market_value",
        aggfunc="sum",
        fill_value=0.0,
    ).reset_index()
    wide_mv.columns = ["snapshot_at"] + [
        f"mv__{slugify(c)}" for c in wide_mv.columns[1:]
    ]
    return wide_mv


def _pivot_allocations(sector_grouped: pd.DataFrame) -> pd.DataFrame:
    wide_alloc = sector_grouped.pivot_table(
        index="snapshot_at",
        columns="sector",
        values="allocation_pct",
        aggfunc="sum",
        fill_value=0.0,
    ).reset_index()
    wide_alloc.columns = ["snapshot_at"] + [
        f"alloc__{slugify(c)}" for c in wide_alloc.columns[1:]
    ]
    return wide_alloc


def _merge_results(
    wide_mv: pd.DataFrame,
    wide_alloc: pd.DataFrame,
    equity_total: pd.DataFrame,
    account_total: pd.DataFrame | None,
) -> pd.DataFrame:
    wide = wide_mv.merge(wide_alloc, on="snapshot_at", how="left")

    equity_total_out = equity_total.copy()
    equity_total_out["snapshot_at"] = equity_total_out["snapshot_at"].astype(
        str
    )

    wide["snapshot_at"] = wide["snapshot_at"].astype(str)
    wide = wide.merge(equity_total_out, on="snapshot_at", how="left")

    if account_total is not None:
        account_total_out = account_total.copy()
        account_total_out["snapshot_at"] = account_total_out[
            "snapshot_at"
        ].astype(str)
        wide = wide.merge(account_total_out, on="snapshot_at", how="left")

    return wide.fillna(0.0)


def main(items: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    if items is None:
        try:
            items = _items  # type: ignore[name-defined]
        except NameError as exc:
            raise NameError("_items is not defined") from exc

    if not items:
        return []

    rows = [it.get("json", it) for it in items]
    if not rows:
        return []

    df = pd.DataFrame(rows)
    _validate_required_columns(df)

    df = _normalize_snapshot_date(df)
    df = _normalize_market_value(df)
    df = _normalize_sector(df)

    account_total = _extract_account_total(df)
    df_equity = _filter_equity_positions(df)

    sector_grouped, equity_total = _calculate_sector_aggregations(df_equity)
    wide_mv = _pivot_market_values(sector_grouped)
    wide_alloc = _pivot_allocations(sector_grouped)

    result = _merge_results(wide_mv, wide_alloc, equity_total, account_total)

    return [{"json": row} for row in result.to_dict(orient="records")]
