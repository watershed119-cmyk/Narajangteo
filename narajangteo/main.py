from __future__ import annotations

import argparse
import sys
from datetime import datetime

from narajangteo.config import load_config
from narajangteo.emailer import build_email, send_email
from narajangteo.g2b import G2BClient
from narajangteo.state import filter_new, load_seen, save_seen


def run_once(*, dry_run: bool = False) -> int:
    config = load_config()
    client = G2BClient(config.api_key)
    notices = client.search_recent(
        config.keywords,
        lookback_days=config.lookback_days,
        num_rows=config.num_rows,
    )
    seen = load_seen(config.state_file)
    new_notices = filter_new(notices, seen)
    message = build_email(config, new_notices, datetime.now())

    if dry_run:
        print(message.get_body(preferencelist=("plain",)).get_content())
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
    args = parser.parse_args(argv)

    try:
        return run_once(dry_run=args.dry_run)
    except Exception as exc:
        print(f"narajangteo failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
