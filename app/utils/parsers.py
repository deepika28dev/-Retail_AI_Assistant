from __future__ import annotations

import json
import re
from datetime import date, datetime
from typing import Any


def normalize_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.lower())


def normalize_text(value: str | None) -> str:
    if value is None:
        return ""
    return " ".join(str(value).strip().lower().split())


def normalize_size(value: str | None) -> str:
    return re.sub(r"\s+", "", str(value or "")).upper()


def parse_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    if isinstance(value, (int, float)):
        return float(value)

    cleaned = str(value).strip().replace("$", "").replace(",", "")
    if not cleaned:
        return None

    try:
        return float(cleaned)
    except ValueError:
        return None


def parse_int(value: Any) -> int | None:
    number = parse_float(value)
    if number is None:
        return None
    return int(number)


def parse_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    text = normalize_text(str(value))
    if text in {"true", "1", "yes", "y", "sale", "clearance"}:
        return True
    if text in {"false", "0", "no", "n", ""}:
        return False
    return False


def parse_date(value: Any) -> date:
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()

    text = str(value).strip()
    patterns = (
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%m/%d/%Y",
        "%m-%d-%Y",
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
    )
    for pattern in patterns:
        try:
            return datetime.strptime(text, pattern).date()
        except ValueError:
            continue
    raise ValueError(f"Unsupported date format: {value}")


def parse_list_field(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]

    text = str(value).strip()
    if not text:
        return []

    if text.startswith("[") and text.endswith("]"):
        try:
            parsed = json.loads(text)
            if isinstance(parsed, list):
                return [str(item).strip() for item in parsed if str(item).strip()]
        except json.JSONDecodeError:
            pass

    for separator in ("|", ";", ",", "/"):
        if separator in text:
            return [item.strip() for item in text.split(separator) if item.strip()]

    return [text]


def parse_stock_map(value: Any) -> dict[str, int]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return {
            normalize_size(str(size)): int(quantity)
            for size, quantity in value.items()
            if parse_int(quantity) is not None
        }

    text = str(value).strip()
    if not text:
        return {}

    if text.startswith("{") and text.endswith("}"):
        try:
            parsed = json.loads(text)
            if isinstance(parsed, dict):
                return {
                    normalize_size(str(size)): int(quantity)
                    for size, quantity in parsed.items()
                    if parse_int(quantity) is not None
                }
        except json.JSONDecodeError:
            pass

    items = re.split(r"[|;,]", text)
    stock_map: dict[str, int] = {}
    for item in items:
        match = re.match(r"\s*([^:=]+)\s*[:=]\s*(-?\d+)\s*$", item)
        if not match:
            continue
        stock_map[normalize_size(match.group(1))] = int(match.group(2))
    return stock_map


def get_row_value(row: dict[str, Any], *candidate_names: str) -> Any:
    normalized_row = {normalize_key(key): value for key, value in row.items()}
    for name in candidate_names:
        if normalize_key(name) in normalized_row:
            return normalized_row[normalize_key(name)]
    return None
