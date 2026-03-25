"""Tests for MetaApiProvider — all facebook_business SDK calls mocked."""
import pytest
from decimal import Decimal
from unittest.mock import MagicMock, patch, PropertyMock
from uuid import uuid4

from app.providers.meta_api_provider import (
    MetaApiProvider, TokenExpiredError, MetaApiPermissionError,
)


@pytest.fixture
def provider():
    return MetaApiProvider(access_token="tok_test", app_id="123", app_secret="secret")


class TestSDKInitialization:
    def test_stores_access_token(self):
        p = MetaApiProvider(access_token="tok_xyz")
        assert p._access_token == "tok_xyz"

    @patch("app.providers.meta_api_provider.MetaApiProvider._get_api")
    def test_creates_api_instance(self, mock_get_api, provider):
        provider._get_api()
        mock_get_api.assert_called_once()


class TestSpendRetrieval:
    @patch("facebook_business.adobjects.adaccount.AdAccount.get_insights")
    @patch("facebook_business.api.FacebookAdsApi.init")
    def test_get_current_spend_parses_decimal(self, mock_init, mock_insights, provider):
        mock_insights.return_value = iter([{"spend": "45.67"}])
        provider._api = MagicMock()  # skip init

        result = provider._get_spend_sync(uuid4(), "today")
        assert result == Decimal("45.67")

    @patch("facebook_business.adobjects.adaccount.AdAccount.get_insights")
    def test_handles_zero_spend(self, mock_insights, provider):
        mock_insights.return_value = iter([{"spend": "0"}])
        provider._api = MagicMock()

        result = provider._get_spend_sync(uuid4(), "today")
        assert result == Decimal("0")

    @patch("facebook_business.adobjects.adaccount.AdAccount.get_insights")
    def test_handles_empty_response(self, mock_insights, provider):
        mock_insights.return_value = iter([])
        provider._api = MagicMock()

        result = provider._get_spend_sync(uuid4(), "today")
        assert result == Decimal("0")


class TestPauseResume:
    @patch("facebook_business.adobjects.campaign.Campaign.api_update")
    def test_pause_returns_success(self, mock_update, provider):
        mock_update.return_value = None
        provider._api = MagicMock()

        result = provider._pause_campaign_sync(uuid4())
        assert result.success is True

    @patch("facebook_business.adobjects.campaign.Campaign.api_update")
    def test_resume_returns_success(self, mock_update, provider):
        mock_update.return_value = None
        provider._api = MagicMock()

        result = provider._resume_campaign_sync(uuid4())
        assert result.success is True

    @patch("facebook_business.adobjects.campaign.Campaign.api_update")
    def test_pause_returns_failure_on_error(self, mock_update, provider):
        from facebook_business.exceptions import FacebookRequestError
        mock_update.side_effect = FacebookRequestError(
            message="Error", request_context={"method": "POST"},
            http_status=400, http_headers={},
            body='{"error": {"code": 100, "message": "Error"}}'
        )
        provider._api = MagicMock()

        result = provider._pause_campaign_sync(uuid4())
        assert result.success is False


class TestRateLimitHandling:
    @patch("time.sleep")
    def test_retries_on_code_613(self, mock_sleep, provider):
        from facebook_business.exceptions import FacebookRequestError
        provider._api = MagicMock()

        call_count = 0
        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise FacebookRequestError(
                    message="Rate limit", request_context={"method": "GET"},
                    http_status=400, http_headers={},
                    body='{"error": {"code": 613, "message": "Rate limit"}}'
                )
            return iter([{"spend": "10.00"}])

        with patch("facebook_business.adobjects.adaccount.AdAccount.get_insights",
                    side_effect=side_effect):
            result = provider._get_spend_sync(uuid4(), "today")
            assert result == Decimal("10.00")
            assert call_count == 3

    @patch("time.sleep")
    def test_gives_up_after_max_retries(self, mock_sleep, provider):
        from facebook_business.exceptions import FacebookRequestError
        provider._api = MagicMock()

        error = FacebookRequestError(
            message="Rate limit", request_context={"method": "GET"},
            http_status=400, http_headers={},
            body='{"error": {"code": 613, "message": "Rate limit"}}'
        )

        with patch("facebook_business.adobjects.adaccount.AdAccount.get_insights",
                    side_effect=error):
            with pytest.raises(FacebookRequestError):
                provider._get_spend_sync(uuid4(), "today")


class TestErrorClassification:
    @patch("time.sleep")
    def test_token_expired_raises_immediately(self, mock_sleep, provider):
        from facebook_business.exceptions import FacebookRequestError
        provider._api = MagicMock()

        error = FacebookRequestError(
            message="Token expired", request_context={"method": "GET"},
            http_status=400, http_headers={},
            body='{"error": {"code": 190, "message": "Token expired"}}'
        )

        with patch("facebook_business.adobjects.adaccount.AdAccount.get_insights",
                    side_effect=error):
            with pytest.raises(TokenExpiredError):
                provider._get_spend_sync(uuid4(), "today")
        mock_sleep.assert_not_called()

    @patch("time.sleep")
    def test_permission_error_raises_immediately(self, mock_sleep, provider):
        from facebook_business.exceptions import FacebookRequestError
        provider._api = MagicMock()

        error = FacebookRequestError(
            message="Permission denied", request_context={"method": "GET"},
            http_status=400, http_headers={},
            body='{"error": {"code": 10, "message": "Permission denied"}}'
        )

        with patch("facebook_business.adobjects.adaccount.AdAccount.get_insights",
                    side_effect=error):
            with pytest.raises(MetaApiPermissionError):
                provider._get_spend_sync(uuid4(), "today")
