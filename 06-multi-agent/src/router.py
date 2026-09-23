"""One deterministic classification decision; this is a router, not a supervisor."""

from typing import Literal


Route = Literal["record", "guideline", "doctor", "refuse"]


def classify_query(query: str) -> Route:
    lowered = query.lower()
    if any(word in lowered for word in ("history", "record", "历史", "记录")):
        return "record"
    if any(word in lowered for word in ("guideline", "guide", "指南")):
        return "guideline"
    if any(word in lowered for word in ("doctor", "specialist", "医生")):
        return "doctor"
    return "refuse"
