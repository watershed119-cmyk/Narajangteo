from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import time
from pathlib import Path


@dataclass(frozen=True)
class AppConfig:
    api_key: str
    keywords: tuple[str, ...]
    recipients: tuple[str, ...]
    smtp_host: str
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_sender: str | None = None
    smtp_use_tls: bool = True
    lookback_days: int = 1
    num_rows: int = 100
    state_file: Path = field(default_factory=lambda: Path(".narajangteo_state.json"))
    digest_time: time = time(hour=7, minute=0)

    @property
    def sender(self) -> str:
        return self.smtp_sender or self.smtp_username or "narajangteo@example.com"


def _split_csv(value: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in value.split(",") if item.strip())


def _bool_env(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def load_config() -> AppConfig:
    api_key = os.getenv("NARA_API_KEY", "").strip()
    keywords = _split_csv(os.getenv("NARA_KEYWORDS", ""))
    recipients = _split_csv(os.getenv("EMAIL_TO", ""))
    smtp_host = os.getenv("SMTP_HOST", "").strip()

    missing = []
    if not api_key:
        missing.append("NARA_API_KEY")
    if not keywords:
        missing.append("NARA_KEYWORDS")
    if not recipients:
        missing.append("EMAIL_TO")
    if not smtp_host:
        missing.append("SMTP_HOST")
    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

    return AppConfig(
        api_key=api_key,
        keywords=keywords,
        recipients=recipients,
        smtp_host=smtp_host,
        smtp_port=int(os.getenv("SMTP_PORT", "587")),
        smtp_username=os.getenv("SMTP_USERNAME") or None,
        smtp_password=os.getenv("SMTP_PASSWORD") or None,
        smtp_sender=os.getenv("SMTP_SENDER") or None,
        smtp_use_tls=_bool_env("SMTP_USE_TLS", True),
        lookback_days=int(os.getenv("LOOKBACK_DAYS", "1")),
        num_rows=int(os.getenv("NARA_NUM_ROWS", "100")),
        state_file=Path(os.getenv("STATE_FILE", ".narajangteo_state.json")),
    )
