"""Data cleanup utilities for portfolio position files."""

import re
from datetime import UTC, datetime
from typing import Any
from zoneinfo import ZoneInfo


def to_number(value: Any) -> float | None:
    """Convert string to number, handling currency and accounting formats."""
    if value is None:
        return None
    s = str(value).strip()
    if not s or s.lower() == "n/a":
        return None
    neg = bool(re.match(r"^\(.*\)$", s))
    s = s.strip("()").replace("$", "").replace(",", "")
    try:
        n = float(s)
    except ValueError:
        return None
    return -n if neg else n


def to_percent(value: Any) -> float | None:
    """Convert percentage string to decimal (e.g., "50%" -> 0.5)."""
    if value is None:
        return None
    s = str(value).strip()
    if not s or s.lower() == "n/a":
        return None
    s = s.replace("%", "").replace(",", "")
    try:
        return float(s) / 100.0
    except ValueError:
        return None


def to_bool(value: Any) -> bool | None:
    """Convert string to boolean (yes/no, true/false)."""
    if value is None:
        return None
    s = str(value).strip().lower()
    if s in {"yes", "y", "true"}:
        return True
    if s in {"no", "n", "false"}:
        return False
    return None


def pick(row: dict[str, Any], *keys: str) -> Any:
    """Pick first non-empty value from row by trying multiple keys."""
    for k in keys:
        if k in row and row[k] not in (None, ""):
            return row[k]
    return None


def _parse_snapshot_metadata(
    filename: str,
) -> tuple[datetime, datetime, datetime]:
    """Parse snapshot date and time from filename."""
    dt = datetime.strptime(
        filename, "Individual-Positions-%Y-%m-%d-%H%M%S.csv"
    ).replace(tzinfo=ZoneInfo("Europe/Madrid"))
    return dt.date(), dt, dt


def _extract_asset_identifiers(
    row: dict[str, Any],
) -> tuple[str, str, str, str]:
    """Extract asset identifiers: (symbol, description, security_type, sector)."""
    symbol = (pick(row, "Symbol", "SYM", "Ticker") or "").strip().upper()
    desc = (
        pick(row, "Description", "Desc", "Security Description") or ""
    ).strip()
    sec_type = (pick(row, "Security Type", "Type") or "").strip()
    sector = (pick(row, "sector", "Sector") or "").strip()
    return symbol, desc, sec_type, sector


def _build_asset_key(symbol: str, desc: str) -> str:
    """Build unique asset key (e.g., "EQUITY:SYMBOL:AAPL")."""
    if symbol:
        return f"EQUITY:SYMBOL:{symbol}"
    return f"UNKNOWN:DESC:{desc}"


def _build_asset_document(
    account_id: str, asset_key: str, row: dict[str, Any]
) -> dict[str, Any]:
    """Build asset document from row data."""
    symbol, desc, sec_type, sector = _extract_asset_identifiers(row)
    return {
        "account_id": account_id,
        "asset_key": asset_key,
        "symbol": symbol or None,
        "name": desc or None,
        "security_type": sec_type or None,
        "sector": sector or None,
        "rating": pick(row, "Ratings", "Rating") or None,
        "updated_at": datetime.now(UTC).isoformat(timespec="seconds") + "Z",
    }


def _extract_basic_position_data(row: dict[str, Any]) -> dict[str, Any]:
    """Extract basic position data (quantity, price, values)."""
    return {
        "quantity": to_number(pick(row, "Qty (Quantity)", "Qty", "Quantity")),
        "price": to_number(pick(row, "Price")),
        "market_value": to_number(
            pick(row, "Mkt Val (Market Value)", "Market Value")
        ),
        "cost_basis": to_number(pick(row, "Cost Basis")),
    }


def _extract_gain_loss_data(row: dict[str, Any]) -> dict[str, Any]:
    """Extract gain/loss metrics."""
    return {
        "gain_abs": to_number(
            pick(row, "Gain $ (Gain/Loss $)", "Gain/Loss $", "Gain $")
        ),
        "gain_pct": to_percent(
            pick(row, "Gain % (Gain/Loss %)", "Gain/Loss %", "Gain %")
        ),
    }


def _extract_change_data(row: dict[str, Any]) -> dict[str, Any]:
    """Extract day and price change metrics."""
    return {
        "day_change_abs": to_number(
            pick(row, "Day Chng $ (Day Change $)", "Day Change $")
        ),
        "day_change_pct": to_percent(
            pick(row, "Day Chng % (Day Change %)", "Day Change %")
        ),
        "price_change_abs": to_number(
            pick(row, "Price Chng $ (Price Change $)", "Price Change $")
        ),
        "price_change_pct": to_percent(
            pick(row, "Price Chng % (Price Change %)", "Price Change %")
        ),
    }


def _extract_market_data(row: dict[str, Any]) -> dict[str, Any]:
    """Extract market data (52w high/low, P/E ratio, reinvestment flags)."""
    return {
        "low_52w": to_number(
            pick(row, "52 Wk Low (52 Week Low)", "52 Week Low")
        ),
        "high_52w": to_number(
            pick(row, "52 Wk High (52 Week High)", "52 Week High")
        ),
        "pe_ratio": to_number(
            pick(row, "P/E Ratio (Price/Earnings Ratio)", "P/E Ratio")
        ),
        "reinvest_dividends": to_bool(pick(row, "Reinvest?")),
        "reinvest_cap_gains": to_bool(pick(row, "Reinvest Capital Gains?")),
    }


def _extract_position_metrics(row: dict[str, Any]) -> dict[str, Any]:
    """Extract all position metrics from row data."""
    return {
        **_extract_basic_position_data(row),
        **_extract_gain_loss_data(row),
        **_extract_change_data(row),
        **_extract_market_data(row),
    }


def _build_position_document(
    metadata: dict[str, Any], row: dict[str, Any]
) -> dict[str, Any]:
    """Build position document from metadata and row data."""
    metrics = _extract_position_metrics(row)
    return {
        **metadata,
        **metrics,
        "imported_at": datetime.now(UTC).isoformat(timespec="seconds") + "Z",
    }


def normalize_schwab_row(
    row: dict[str, Any], account_id: str = "schwab-1"
) -> dict[str, Any] | None:
    """Normalize Schwab position CSV row into structured document."""
    source_file_name = row.get("filename")
    source_file_id = row.get("source_file_id")
    snapshot_date, snapshot_at, _ = _parse_snapshot_metadata(source_file_name)

    symbol, desc, _, _ = _extract_asset_identifiers(row)
    if not symbol and not desc:
        return None

    asset_key = _build_asset_key(symbol, desc)
    doc_id = f"{account_id}|{asset_key}|{source_file_name}"

    asset_doc = _build_asset_document(account_id, asset_key, row)

    position_metadata = {
        "account_id": account_id,
        "asset_key": asset_key,
        "snapshot_date": snapshot_date,
        "snapshot_at": snapshot_at,
    }
    position_doc = _build_position_document(position_metadata, row)

    return {
        "doc_id": doc_id,
        "account_id": account_id,
        "asset_key": asset_key,
        "snapshot_date": snapshot_date,
        "snapshot_at": snapshot_at,
        "source_file_id": source_file_id,
        "source_file_name": source_file_name,
        "asset": asset_doc,
        "position": position_doc,
    }


def cleanup_raw_data_for_storage(
    items: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Clean and normalize raw position data for storage."""
    if items is None:
        try:
            items = _items  # type: ignore[name-defined]
        except NameError as exc:
            raise NameError("_items is not defined") from exc

    clean_docs = []
    for item in items:
        row_data = item["json"]
        normalized = normalize_schwab_row(row_data)
        if normalized is not None:
            clean_docs.append(normalized)

    return clean_docs
