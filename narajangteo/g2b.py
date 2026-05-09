from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Protocol
from urllib.parse import urlencode
from urllib.request import urlopen

API_URL = "https://apis.data.go.kr/1230000/ad/BidPublicInfoService/getBidPblancListInfoServcPPSSrch"


@dataclass(frozen=True)
class BidNotice:
    keyword: str
    notice_no: str
    notice_order: str
    title: str
    agency: str
    demand_agency: str
    budget: str
    notice_date: str
    bid_start: str
    bid_close: str
    opening_date: str
    method: str
    contract_method: str
    detail_url: str

    @property
    def identity(self) -> str:
        return f"{self.notice_no}-{self.notice_order}"


class HttpResponse(Protocol):
    def raise_for_status(self) -> None: ...

    def json(self) -> dict[str, Any]: ...


class HttpSession(Protocol):
    def get(self, url: str, params: dict[str, Any], timeout: int) -> HttpResponse: ...


class UrllibResponse:
    def __init__(self, status: int, body: bytes) -> None:
        self.status = status
        self.body = body

    def raise_for_status(self) -> None:
        if self.status >= 400:
            raise RuntimeError(f"HTTP request failed with status {self.status}")

    def json(self) -> dict[str, Any]:
        return json.loads(self.body.decode("utf-8"))


class UrllibSession:
    def get(self, url: str, params: dict[str, Any], timeout: int) -> UrllibResponse:
        request_url = f"{url}?{urlencode(params)}"
        with urlopen(request_url, timeout=timeout) as response:
            return UrllibResponse(response.status, response.read())


class G2BClient:
    def __init__(self, api_key: str, session: HttpSession | None = None) -> None:
        self.api_key = api_key
        self.session = session or UrllibSession()

    def search_keyword(
        self,
        keyword: str,
        start: datetime,
        end: datetime,
        *,
        num_rows: int = 100,
    ) -> list[BidNotice]:
        params = {
            "serviceKey": self.api_key,
            "pageNo": 1,
            "numOfRows": num_rows,
            "inqryDiv": 1,
            "inqryBgnDt": start.strftime("%Y%m%d%H%M"),
            "inqryEndDt": end.strftime("%Y%m%d%H%M"),
            "bidNtceNm": keyword,
            "type": "json",
        }
        response = self.session.get(API_URL, params=params, timeout=30)
        response.raise_for_status()
        payload = response.json()
        return parse_notices(payload, keyword)

    def search_recent(
        self,
        keywords: tuple[str, ...],
        *,
        lookback_days: int = 1,
        num_rows: int = 100,
        now: datetime | None = None,
    ) -> list[BidNotice]:
        end = now or datetime.now()
        start = end - timedelta(days=lookback_days)
        notices: list[BidNotice] = []
        for keyword in keywords:
            notices.extend(self.search_keyword(keyword, start, end, num_rows=num_rows))
        return deduplicate_notices(notices)


def parse_notices(payload: dict[str, Any], keyword: str) -> list[BidNotice]:
    header = payload.get("response", {}).get("header", {})
    result_code = str(header.get("resultCode", "00"))
    if result_code not in {"00", "0"}:
        message = header.get("resultMsg", "Unknown API error")
        raise RuntimeError(f"나라장터 API error {result_code}: {message}")

    raw_items = payload.get("response", {}).get("body", {}).get("items", [])
    if isinstance(raw_items, dict):
        raw_items = [raw_items]

    notices = []
    for item in raw_items or []:
        notices.append(
            BidNotice(
                keyword=keyword,
                notice_no=str(item.get("bidNtceNo", "")),
                notice_order=str(item.get("bidNtceOrd", "")),
                title=str(item.get("bidNtceNm", "")),
                agency=str(item.get("ntceInsttNm", "")),
                demand_agency=str(item.get("dminsttNm", "")),
                budget=str(item.get("asignBdgtAmt", "")),
                notice_date=str(item.get("bidNtceDt", "")),
                bid_start=str(item.get("bidBeginDt", "")),
                bid_close=str(item.get("bidClseDt", "")),
                opening_date=str(item.get("opengDt", "")),
                method=str(item.get("bidMethdNm", "")),
                contract_method=str(item.get("cntrctCnclsMthdNm", "")),
                detail_url=str(item.get("bidNtceDtlUrl", "")),
            )
        )
    return notices


def deduplicate_notices(notices: list[BidNotice]) -> list[BidNotice]:
    seen: set[str] = set()
    unique = []
    for notice in notices:
        if notice.identity in seen:
            continue
        seen.add(notice.identity)
        unique.append(notice)
    return unique
