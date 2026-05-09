from datetime import datetime

from narajangteo.config import AppConfig
from narajangteo.emailer import build_email, format_budget
from narajangteo.g2b import BidNotice


def test_format_budget_adds_commas_and_currency():
    assert format_budget("1234567") == "1,234,567원"
    assert format_budget("") == "-"


def test_build_email_contains_notice_summary():
    config = AppConfig(
        api_key="key",
        keywords=("AI",),
        recipients=("to@example.com",),
        smtp_host="smtp.example.com",
        smtp_username="from@example.com",
    )
    notice = BidNotice(
        keyword="AI",
        notice_no="20260123456",
        notice_order="000",
        title="AI 플랫폼 구축",
        agency="공고기관",
        demand_agency="수요기관",
        budget="1000000",
        notice_date="2026-05-09 09:00:00",
        bid_start="2026-05-09 10:00:00",
        bid_close="2026-05-10 10:00:00",
        opening_date="2026-05-10 11:00:00",
        method="전자입찰",
        contract_method="제한경쟁",
        detail_url="https://example.com/bid",
    )

    message = build_email(config, [notice], datetime(2026, 5, 9, 7, 0))
    text = message.get_body(preferencelist=("plain",)).get_content()

    assert "[나라장터] 키워드 입찰공고 1건" in message["Subject"]
    assert "AI 플랫폼 구축" in text
    assert "1,000,000원" in text
    assert "https://example.com/bid" in text
