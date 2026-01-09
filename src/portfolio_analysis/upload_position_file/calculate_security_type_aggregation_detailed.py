import re
from typing import Any

import pandas as pd

TOTAL_KEY = "--"
EQUITY_ASSET_PREFIX = "EQUITY:"
DROP_UNKNOWN_SECTOR = True


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


def _normalize_numeric_columns(df: pd.DataFrame) -> pd.DataFrame:
    df["snapshot_at"] = pd.to_datetime(df["snapshot_at"], errors="coerce")
    df["market_value"] = pd.to_numeric(
        df["market_value"], errors="coerce"
    ).fillna(0.0)

    if "quantity" not in df.columns:
        df["quantity"] = 0
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce").fillna(0.0)
    return df


def _normalize_text_columns(df: pd.DataFrame) -> pd.DataFrame:
    if "sector" not in df.columns:
        df["sector"] = ""
    df["sector"] = df["sector"].fillna("").astype(str).str.strip()

    for col in ["symbol", "name"]:
        if col not in df.columns:
            df[col] = None
    return df


def _normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    df = _normalize_numeric_columns(df)
    df = _normalize_text_columns(df)
    return df


def _extract_account_total(df: pd.DataFrame) -> pd.DataFrame | None:
    if "security_type" not in df.columns:
        return None
    totals = df[df["security_type"] == TOTAL_KEY].copy()
    if totals.empty:
        return None
    return totals.groupby("snapshot_at", as_index=False).agg(
        mv__account_total=("market_value", "sum")
    )


def _create_account_total_map(
    account_total: pd.DataFrame | None,
) -> dict[Any, float]:
    if account_total is None or account_total.empty:
        return {}
    return {
        r["snapshot_at"]: float(r["mv__account_total"])
        for r in account_total.to_dict(orient="records")
    }


def _filter_equity_positions(df: pd.DataFrame) -> pd.DataFrame:
    df_positions = df.copy()
    if "security_type" in df_positions.columns:
        df_positions = df_positions[df_positions["security_type"] != TOTAL_KEY]

    df_equity = df_positions[
        df_positions["asset_key"].astype(str).str.startswith(EQUITY_ASSET_PREFIX)
    ].copy()

    if DROP_UNKNOWN_SECTOR:
        df_equity = df_equity[df_equity["sector"] != ""]
    else:
        df_equity.loc[df_equity["sector"] == "", "sector"] = "unknown"

    return df_equity


def _calculate_totals(
    df_equity: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    equity_totals = df_equity.groupby("snapshot_at", as_index=False).agg(
        mv__equity_total=("market_value", "sum")
    )
    sector_totals = df_equity.groupby(
        ["snapshot_at", "sector"], as_index=False
    ).agg(sector_market_value=("market_value", "sum"))
    return equity_totals, sector_totals


def _enrich_with_allocations(
    df_equity: pd.DataFrame,
    equity_totals: pd.DataFrame,
    sector_totals: pd.DataFrame,
) -> pd.DataFrame:
    df_equity = df_equity.merge(
        equity_totals, on="snapshot_at", how="left"
    ).merge(sector_totals, on=["snapshot_at", "sector"], how="left")

    df_equity["alloc_of_equity"] = (
        df_equity["market_value"] / df_equity["mv__equity_total"]
    ).fillna(0.0)
    df_equity["alloc_of_sector"] = (
        df_equity["market_value"] / df_equity["sector_market_value"]
    ).fillna(0.0)

    return df_equity


def _aggregate_holdings_by_symbol(df_sector: pd.DataFrame) -> pd.DataFrame:
    return (
        df_sector.groupby(["symbol", "name", "sector"], as_index=False)
        .agg(
            market_value=("market_value", "sum"),
            quantity=("quantity", "sum"),
            alloc_of_equity=("alloc_of_equity", "sum"),
            alloc_of_sector=("alloc_of_sector", "sum"),
        )
        .sort_values("market_value", ascending=False)
    )


def _build_holding_dict(
    row: pd.Series, account_total_val: float
) -> dict[str, Any]:
    mv = float(row.get("market_value", 0.0))
    alloc_of_account = (mv / account_total_val) if account_total_val else 0.0

    return {
        "symbol": row.get("symbol"),
        "name": row.get("name"),
        "quantity": float(row.get("quantity", 0.0)),
        "market_value": mv,
        "alloc_of_equity": float(row.get("alloc_of_equity", 0.0)),
        "alloc_of_sector": float(row.get("alloc_of_sector", 0.0)),
        "alloc_of_account": float(alloc_of_account),
    }


def _calculate_sector_allocations(
    sec_mv: float, equity_total: float, account_total_val: float
) -> tuple[float, float]:
    sec_alloc_equity = (sec_mv / equity_total) if equity_total else 0.0
    sec_alloc_account = (sec_mv / account_total_val) if account_total_val else 0.0
    return sec_alloc_equity, sec_alloc_account


def _build_sector_dict(
    sector_name: str,
    sec_mv: float,
    sec_alloc_equity: float,
    sec_alloc_account: float,
    holdings: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "sector": sector_name,
        "market_value": sec_mv,
        "alloc_pct_of_equity": float(sec_alloc_equity),
        "alloc_pct_of_account": float(sec_alloc_account),
        "holdings": holdings,
    }


def _build_holdings_list(
    sec_df_aggregated: pd.DataFrame, account_total_val: float
) -> list[dict[str, Any]]:
    return [
        _build_holding_dict(row, account_total_val)
        for _, row in sec_df_aggregated.iterrows()
    ]


def _process_sector(
    sector_name: str,
    sec_df: pd.DataFrame,
    equity_total: float,
    account_total_val: float,
) -> tuple[str, dict[str, Any]]:
    sec_mv = float(sec_df["sector_market_value"].iloc[0])
    sec_df_aggregated = _aggregate_holdings_by_symbol(sec_df)
    holdings = _build_holdings_list(sec_df_aggregated, account_total_val)

    sec_alloc_equity, sec_alloc_account = _calculate_sector_allocations(
        sec_mv, equity_total, account_total_val
    )

    sector_dict = _build_sector_dict(
        sector_name, sec_mv, sec_alloc_equity, sec_alloc_account, holdings
    )

    return slugify(sector_name), sector_dict


def _process_snapshot(
    snap_df: pd.DataFrame, acct_map: dict[Any, float], snap_at: Any
) -> dict[str, Any]:
    equity_total = float(snap_df["mv__equity_total"].iloc[0])
    account_total_val = float(acct_map.get(snap_at, 0.0))

    sectors_obj = {
        key: value
        for sector_name, sec_df in snap_df.groupby("sector", sort=False)
        for key, value in [
            _process_sector(sector_name, sec_df, equity_total, account_total_val)
        ]
    }

    return {
        "snapshot_at": str(snap_at),
        "mv__equity_total": equity_total,
        "mv__account_total": account_total_val,
        "sectors": sectors_obj,
    }


def _build_empty_result(account_total: pd.DataFrame | None) -> list[dict[str, Any]]:
    if account_total is None or account_total.empty:
        return []

    tmp = account_total.copy()
    tmp["snapshot_at"] = tmp["snapshot_at"].astype(str)
    return [
        {
            "json": {
                **r,
                "mv__equity_total": 0.0,
                "sectors": {},
            }
        }
        for r in tmp.to_dict(orient="records")
    ]


def _get_items(items: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    if items is None:
        try:
            items = _items  # type: ignore[name-defined]
        except NameError as exc:
            raise NameError("_items is not defined") from exc
    return items


def _prepare_dataframe(items: list[dict[str, Any]]) -> pd.DataFrame:
    rows = [it.get("json", it) for it in items]
    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    _validate_required_columns(df)
    return _normalize_dataframe(df)


def _process_equity_data(
    df_equity: pd.DataFrame, acct_map: dict[Any, float]
) -> list[dict[str, Any]]:
    equity_totals, sector_totals = _calculate_totals(df_equity)
    df_equity = _enrich_with_allocations(df_equity, equity_totals, sector_totals)

    return [
        _process_snapshot(snap_df, acct_map, snap_at)
        for snap_at, snap_df in df_equity.groupby("snapshot_at", sort=False)
    ]


def main(items: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    items = _get_items(items)
    df = _prepare_dataframe(items)
    if df.empty:
        return []

    account_total = _extract_account_total(df)
    acct_map = _create_account_total_map(account_total)

    df_equity = _filter_equity_positions(df)
    if df_equity.empty:
        return _build_empty_result(account_total)

    out_items = _process_equity_data(df_equity, acct_map)
    return [{"json": row} for row in out_items]
