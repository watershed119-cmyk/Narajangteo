from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from narajangteo.config import AppConfig
from narajangteo.g2b import BidNotice
from narajangteo.main import run_once


def sample_config(tmp_path: Path) -> AppConfig:
    return AppConfig(
        api_key="secret",
        keywords=("AI",),
        recipients=("user@example.com",),
        smtp_host="smtp.example.com",
        state_file=tmp_path / "state.json",
    )


def sample_notice() -> BidNotice:
    return BidNotice(
        keyword="AI",
        notice_no="20260123456",
        notice_order="000",
        title="AI 플랫폼 구축",
        agency="발주기관",
        demand_agency="수요기관",
        budget="1000000",
        notice_date="2026-05-30",
        bid_start="2026-05-30",
        bid_close="2026-06-01",
        opening_date="2026-06-02",
        method="일반",
        contract_method="일반",
        detail_url="https://example.com/bid",
    )


def excluded_notice() -> BidNotice:
    return BidNotice(
        keyword="AI",
        notice_no="20260123457",
        notice_order="000",
        title="시설 유지보수 용역",
        agency="발주기관",
        demand_agency="수요기관",
        budget="1000000",
        notice_date="2026-05-30",
        bid_start="2026-05-30",
        bid_close="2026-06-01",
        opening_date="2026-06-02",
        method="일반",
        contract_method="일반",
        detail_url="https://example.com/bid2",
    )


@patch("narajangteo.main.load_seen", return_value=set())
@patch("narajangteo.main.send_email")
@patch("narajangteo.main.G2BClient")
@patch("narajangteo.main.load_config")
def test_run_once_skips_email_when_no_new_notices(
    mock_load_config, mock_client_cls, mock_send_email, mock_load_seen, capsys
):
    with TemporaryDirectory() as tmp_dir:
        mock_load_config.return_value = sample_config(Path(tmp_dir) / "state.json")
        mock_client_cls.return_value.search_recent.return_value = []

        assert run_once() == 0

    mock_send_email.assert_not_called()
    assert "No new notices; email skipped" in capsys.readouterr().out


@patch("narajangteo.main.save_seen")
@patch("narajangteo.main.load_seen")
@patch("narajangteo.main.send_email")
@patch("narajangteo.main.G2BClient")
@patch("narajangteo.main.load_config")
def test_run_once_sends_email_when_new_notices_exist(
    mock_load_config,
    mock_client_cls,
    mock_send_email,
    mock_load_seen,
    mock_save_seen,
    capsys,
):
    notice = sample_notice()
    with TemporaryDirectory() as tmp_dir:
        mock_load_config.return_value = sample_config(Path(tmp_dir) / "state.json")
        mock_client_cls.return_value.search_recent.return_value = [notice]
        mock_load_seen.return_value = set()

        assert run_once() == 0

    mock_send_email.assert_called_once()
    mock_save_seen.assert_called_once()
    assert "Sent 1 new notice(s)" in capsys.readouterr().out


@patch("narajangteo.main.load_seen", return_value=set())
@patch("narajangteo.main.send_email")
@patch("narajangteo.main.G2BClient")
@patch("narajangteo.main.load_config")
def test_run_once_force_sends_email_when_no_new_notices(
    mock_load_config, mock_client_cls, mock_send_email, mock_load_seen
):
    with TemporaryDirectory() as tmp_dir:
        mock_load_config.return_value = sample_config(Path(tmp_dir) / "state.json")
        mock_client_cls.return_value.search_recent.return_value = []

        assert run_once(force_send_empty=True) == 0

    mock_send_email.assert_called_once()


@patch("narajangteo.main.save_seen")
@patch("narajangteo.main.load_seen")
@patch("narajangteo.main.send_email")
@patch("narajangteo.main.G2BClient")
@patch("narajangteo.main.load_config")
def test_run_once_excludes_notices_by_title_keyword(
    mock_load_config,
    mock_client_cls,
    mock_send_email,
    mock_load_seen,
    mock_save_seen,
    capsys,
):
    notice = sample_notice()
    notice_to_exclude = excluded_notice()
    with TemporaryDirectory() as tmp_dir:
        config = sample_config(Path(tmp_dir) / "state.json")
        mock_load_config.return_value = AppConfig(
            api_key=config.api_key,
            keywords=config.keywords,
            recipients=config.recipients,
            exclude_keywords=("유지보수",),
            smtp_host=config.smtp_host,
            state_file=config.state_file,
        )
        mock_client_cls.return_value.search_recent.return_value = [notice, notice_to_exclude]
        mock_load_seen.return_value = set()

        assert run_once() == 0

    mock_send_email.assert_called_once()
    mock_save_seen.assert_called_once()
    assert "Sent 1 new notice(s)" in capsys.readouterr().out
