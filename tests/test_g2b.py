from datetime import datetime

from narajangteo.g2b import G2BClient, deduplicate_notices, parse_notices


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


class FakeSession:
    def __init__(self, payload):
        self.payload = payload
        self.calls = []

    def get(self, url, params, timeout):
        self.calls.append({"url": url, "params": params, "timeout": timeout})
        return FakeResponse(self.payload)


def sample_payload():
    return {
        "response": {
            "header": {"resultCode": "00", "resultMsg": "NORMAL SERVICE."},
            "body": {
                "items": [
                    {
                        "bidNtceNo": "20260123456",
                        "bidNtceOrd": "000",
                        "bidNtceNm": "AI 플랫폼 구축",
                        "dminsttNm": "테스트기관",
                        "asignBdgtAmt": "1000000",
                        "bidClseDt": "2026-05-10 10:00:00",
                        "bidNtceDtlUrl": "https://example.com/bid",
                    }
                ]
            },
        }
    }


def test_parse_notices_maps_required_fields():
    notices = parse_notices(sample_payload(), "AI")

    assert len(notices) == 1
    assert notices[0].identity == "20260123456-000"
    assert notices[0].title == "AI 플랫폼 구축"
    assert notices[0].keyword == "AI"


def test_search_keyword_sends_expected_params():
    session = FakeSession(sample_payload())
    client = G2BClient("secret", session=session)

    notices = client.search_keyword(
        "AI",
        datetime(2026, 5, 8, 0, 0),
        datetime(2026, 5, 9, 7, 0),
        num_rows=50,
    )

    params = session.calls[0]["params"]
    assert notices[0].title == "AI 플랫폼 구축"
    assert params["serviceKey"] == "secret"
    assert params["inqryBgnDt"] == "202605080000"
    assert params["inqryEndDt"] == "202605090700"
    assert params["bidNtceNm"] == "AI"
    assert params["type"] == "json"
    assert params["numOfRows"] == 50


def test_deduplicate_notices_keeps_first_identity():
    notice = parse_notices(sample_payload(), "AI")[0]

    assert deduplicate_notices([notice, notice]) == [notice]
