from __future__ import annotations

import re
from pathlib import Path

from app.utils.parsers import normalize_text


NEGATIVE_RULE_SIGNALS = (
    "not eligible",
    "cannot be returned",
    "can't be returned",
    "not returnable",
    "no returns",
    "return not allowed",
)

EXCHANGE_ONLY_SIGNALS = (
    "exchange only",
    "only exchange",
    "eligible for exchange only",
)


class PolicyRepository:
    def __init__(self, policy_path: Path):
        self.policy_path = policy_path
        self.raw_text = self.policy_path.read_text(encoding="utf-8-sig")
        self.segments = self._split_segments(self.raw_text)

    def _split_segments(self, text: str) -> list[str]:
        segments: list[str] = []
        for line in text.splitlines():
            cleaned = line.strip(" -\t")
            if not cleaned:
                continue
            sentence_parts = re.split(r"(?<=[.!?])\s+", cleaned)
            for sentence in sentence_parts:
                stripped = sentence.strip()
                if stripped:
                    segments.append(stripped)
        return segments

    def find_normal_return_clause(self) -> str | None:
        preferred_matches = [
            self._expanded_segment(index)
            for index, segment in enumerate(self.segments)
            if "return" in normalize_text(segment)
            and ("normal" in normalize_text(segment) or "standard" in normalize_text(segment))
        ]
        if preferred_matches:
            return preferred_matches[0]

        for index, segment in enumerate(self.segments):
            text = normalize_text(segment)
            if "return window" in text or ("return" in text and "day" in text):
                return self._expanded_segment(index)
        return None

    def find_keyword_clause(self, keyword: str) -> str | None:
        keyword_normalized = normalize_text(keyword)
        for index, segment in enumerate(self.segments):
            if keyword_normalized in normalize_text(segment):
                return self._expanded_segment(index)
        return None

    def find_vendor_clauses(self, vendor: str) -> list[str]:
        vendor_normalized = normalize_text(vendor)
        return [
            self._expanded_segment(index)
            for index, segment in enumerate(self.segments)
            if vendor_normalized and vendor_normalized in normalize_text(segment)
        ]

    def find_exchange_clause(self) -> str | None:
        for index, segment in enumerate(self.segments):
            if "exchange" in normalize_text(segment):
                return self._expanded_segment(index)
        return None

    def extract_days(self, clause: str | None) -> int | None:
        if not clause:
            return None
        match = re.search(r"(\d+)\s*(calendar|business|working)?\s*day", clause, flags=re.IGNORECASE)
        if not match:
            return None
        return int(match.group(1))

    def blocks_return(self, clause: str | None) -> bool:
        if not clause:
            return False
        normalized_clause = normalize_text(clause)
        return any(signal in normalized_clause for signal in NEGATIVE_RULE_SIGNALS)

    def is_exchange_only(self, clause: str | None) -> bool:
        if not clause:
            return False
        normalized_clause = normalize_text(clause)
        return any(signal in normalized_clause for signal in EXCHANGE_ONLY_SIGNALS)

    def _expanded_segment(self, index: int) -> str:
        current = self.segments[index]
        if index + 1 >= len(self.segments):
            return current

        next_segment = self.segments[index + 1]
        current_text = normalize_text(current)

        if current.endswith(":"):
            return f"{current} {next_segment}"

        if "day" not in current_text and any(
            keyword in current_text
            for keyword in ("return", "sale", "clearance", "exchange", "vendor", "exception")
        ):
            return f"{current} {next_segment}"

        return current
