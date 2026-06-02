from __future__ import annotations

import argparse
import sys
from datetime import datetime

from narajangteo.config import load_config
from narajangteo.emailer import build_email, send_email
from narajangteo.g2b import G2BClient
from narajangteo.state import filter_new, load_seen, save_seen


def _filter_excluded_titles(
    notices: list, exclude_keywords: tuple[str, ...]
) -> tuple[list, int]:
    if not exclude_keywords:
        return notices, 0
    excluded = 0
    filtered = []
    lowered_keywords = tuple(keyword.lower() for keyword in exclude_keywords)
    for notice in notices:
        title = (notice.title or "").lower()
        if any(keyword in title for keyword in lowered_keywords):
            excluded += 1
            continue
        filtered.append(notice)
    return filtered, excluded


def run_once(*, dry_run: bool = False, force_send_empty: bool = False) -> int:
    config = load_config()
    client = G2BClient(config.api_key)
    notices = client.search_recent(
        config.keywords,
        lookback_days=config.lookback_days,
        num_rows=config.num_rows,
    )
    seen = load_seen(config.state_file)
    new_notices = filter_new(notices, seen)
    new_notices, excluded_count = _filter_excluded_titles(
        new_notices, config.exclude_keywords
    )
    message = build_email(config, new_notices, datetime.now())

    if dry_run:
        print(message.get_body(preferencelist=("plain",)).get_content())
        if excluded_count:
            print(f"Excluded {excluded_count} notice(s) by NARA_EXCLUDE_KEYWORDS")
        return 0

    if not new_notices and not force_send_empty:
        if excluded_count:
            print(
                "No new notices after exclusion; email skipped "
                f"(excluded={excluded_count})"
            )
        else:
            print("No new notices; email skipped")
        return 0

    send_email(config, message)
    seen.update(notice.identity for notice in new_notices)
    save_seen(config.state_file, seen)
    print(f"Sent {len(new_notices)} new notice(s) to {', '.join(config.recipients)}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Send a daily 나라장터 keyword bid digest by email."
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Print the digest instead of sending email."
    )
    parser.add_argument(
        "--force-send-empty",
        action="store_true",
        help="Send a test email even when there are no new notices.",
    )
    args = parser.parse_args(argv)

    try:
        return run_once(dry_run=args.dry_run, force_send_empty=args.force_send_empty)
    except Exception as exc:
        print(f"narajangteo failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
