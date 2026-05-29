from __future__ import annotations

import json
from pathlib import Path

from narajangteo.g2b import BidNotice


def load_seen(path: Path) -> set[str]:
    if not path.exists():
        return set()
    data = json.loads(path.read_text(encoding="utf-8"))
    return set(data.get("seen_notice_ids", []))


def save_seen(path: Path, seen: set[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"seen_notice_ids": sorted(seen)}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def filter_new(notices: list[BidNotice], seen: set[str]) -> list[BidNotice]:
    return [notice for notice in notices if notice.identity not in seen]
