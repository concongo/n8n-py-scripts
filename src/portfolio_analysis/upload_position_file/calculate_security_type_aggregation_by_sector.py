import re

import pandas as pd

TOTAL_KEY = "--"

# --- knobs you can tweak ---
DROP_UNKNOWN_SECTOR = True  # if True, excludes rows with missing/blank sector
EQUITY_ASSET_PREFIX = (
    "EQUITY:"  # uses asset_key prefix instead of security_type
)
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


def main(items):
    rows = [it.get("json", it) for it in (items or [])]
    if not rows:
        return []

    df = pd.DataFrame(rows)

    for required in ["snapshot_at", "market_value"]:
        if required not in df.columns:
            raise ValueError(f"Missing '{required}' in input items")

    # Normalize date + numeric
    df["snapshot_at"] = pd.to_datetime(df["snapshot_at"], errors="coerce")
    df["market_value"] = pd.to_numeric(
        df["market_value"], errors="coerce"
    ).fillna(0.0)

    # Normalize sector
    if "sector" not in df.columns:
        df["sector"] = None
    df["sector"] = df["sector"].astype("object")
    df["sector"] = df["sector"].where(df["sector"].notna(), "")
    df["sector"] = df["sector"].astype(str).str.strip()

    # Account total (from Schwab total row) if present
    account_total = None
    if "security_type" in df.columns:
        totals = df[df["security_type"] == TOTAL_KEY]
        if not totals.empty:
            account_total = totals.groupby("snapshot_at", as_index=False).agg(
                mv__account_total=("market_value", "sum")
            )

    # --- Equity filter: asset_key startswith EQUITY: ---
    if "asset_key" not in df.columns:
        raise ValueError(
            "Missing 'asset_key' in input items (needed for robust equity filtering)"
        )

    df_positions = df.copy()
    if "security_type" in df_positions.columns:
        df_positions = df_positions[df_positions["security_type"] != TOTAL_KEY]

    df_equity = df_positions[
        df_positions["asset_key"]
        .astype(str)
        .str.startswith(EQUITY_ASSET_PREFIX)
    ].copy()

    # Optionally drop unknown sectors
    if DROP_UNKNOWN_SECTOR:
        df_equity = df_equity[df_equity["sector"] != ""]

    # If sector still empty (and DROP_UNKNOWN_SECTOR is False), label as "unknown"
    df_equity.loc[df_equity["sector"] == "", "sector"] = "unknown"

    # 1) Sector totals per date (Equity only)
    sector_grouped = df_equity.groupby(
        ["snapshot_at", "sector"], as_index=False
    ).agg(market_value=("market_value", "sum"))

    # 2) Equity denominator per date (so alloc sums to ~1)
    denom = df_equity.groupby("snapshot_at", as_index=False).agg(
        mv__equity_total=("market_value", "sum")
    )

    sector_grouped = sector_grouped.merge(denom, on="snapshot_at", how="left")
    sector_grouped["allocation_pct"] = (
        sector_grouped["market_value"] / sector_grouped["mv__equity_total"]
    ).fillna(0.0)

    # 3) Pivot market_value by sector
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

    # 4) Pivot allocation by sector
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

    # 5) Merge wide frames + totals
    wide = wide_mv.merge(wide_alloc, on="snapshot_at", how="left")

    denom_out = denom.copy()
    denom_out["snapshot_at"] = denom_out["snapshot_at"].astype(str)

    wide["snapshot_at"] = wide["snapshot_at"].astype(str)
    wide = wide.merge(denom_out, on="snapshot_at", how="left")

    if account_total is not None:
        account_total["snapshot_at"] = account_total["snapshot_at"].astype(str)
        wide = wide.merge(account_total, on="snapshot_at", how="left")

    wide = wide.fillna(0.0)

    out = wide.to_dict(orient="records")
    return [{"json": row} for row in out]
