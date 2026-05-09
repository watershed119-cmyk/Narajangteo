from __future__ import annotations

import smtplib
from collections.abc import Sequence
from datetime import datetime
from email.message import EmailMessage
from html import escape

from narajangteo.config import AppConfig
from narajangteo.g2b import BidNotice


def format_budget(value: str) -> str:
    if not value:
        return "-"
    try:
        return f"{int(float(value)):,}원"
    except ValueError:
        return value


def build_email(
    config: AppConfig, notices: Sequence[BidNotice], generated_at: datetime
) -> EmailMessage:
    subject = f"[나라장터] 키워드 입찰공고 {len(notices)}건 ({generated_at:%Y-%m-%d})"
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = config.sender
    message["To"] = ", ".join(config.recipients)

    text_lines = [
        f"나라장터 키워드 입찰공고 {len(notices)}건",
        f"생성시각: {generated_at:%Y-%m-%d %H:%M}",
        "",
    ]
    for index, notice in enumerate(notices, start=1):
        text_lines.extend(
            [
                f"{index}. [{notice.keyword}] {notice.title}",
                f"   공고번호: {notice.identity}",
                f"   수요기관: {notice.demand_agency or '-'}",
                f"   예산: {format_budget(notice.budget)}",
                f"   마감: {notice.bid_close or '-'}",
                f"   링크: {notice.detail_url or '-'}",
                "",
            ]
        )
    if not notices:
        text_lines.append("조건에 맞는 신규 입찰공고가 없습니다.")

    message.set_content("\n".join(text_lines))
    message.add_alternative(_build_html(notices, generated_at), subtype="html")
    return message


def _build_html(notices: Sequence[BidNotice], generated_at: datetime) -> str:
    rows = []
    for notice in notices:
        title = escape(notice.title or "-")
        url = escape(notice.detail_url or "")
        title_cell = f'<a href="{url}">{title}</a>' if url else title
        rows.append(
            "<tr>"
            f"<td>{escape(notice.keyword)}</td>"
            f"<td>{title_cell}</td>"
            f"<td>{escape(notice.demand_agency or '-')}</td>"
            f"<td>{escape(format_budget(notice.budget))}</td>"
            f"<td>{escape(notice.bid_close or '-')}</td>"
            f"<td>{escape(notice.method or '-')}</td>"
            "</tr>"
        )

    body = "".join(rows) or '<tr><td colspan="6">조건에 맞는 신규 입찰공고가 없습니다.</td></tr>'
    return f"""
<!doctype html>
<html lang="ko">
  <body>
    <h2>나라장터 키워드 입찰공고 {len(notices)}건</h2>
    <p>생성시각: {generated_at:%Y-%m-%d %H:%M}</p>
    <table border="1" cellpadding="6" cellspacing="0">
      <thead>
        <tr>
          <th>키워드</th><th>공고명</th><th>수요기관</th><th>예산</th><th>입찰마감</th><th>방식</th>
        </tr>
      </thead>
      <tbody>{body}</tbody>
    </table>
  </body>
</html>
""".strip()


def send_email(config: AppConfig, message: EmailMessage) -> None:
    with smtplib.SMTP(config.smtp_host, config.smtp_port, timeout=30) as smtp:
        if config.smtp_use_tls:
            smtp.starttls()
        if config.smtp_username and config.smtp_password:
            smtp.login(config.smtp_username, config.smtp_password)
        smtp.send_message(message)
