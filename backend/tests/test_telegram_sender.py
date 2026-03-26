"""Tests for TelegramSender."""
from unittest.mock import patch, MagicMock

import pytest

from app.alerts.telegram_sender import TelegramSender


class TestTelegramSenderInit:
    def test_default_no_token(self):
        sender = TelegramSender(bot_token="")
        assert sender._bot_token == ""

    def test_custom_token(self):
        sender = TelegramSender(bot_token="123:ABC")
        assert sender._bot_token == "123:ABC"

    def test_base_url(self):
        sender = TelegramSender(bot_token="123:ABC")
        assert sender._base_url == "https://api.telegram.org/bot123:ABC"


class TestSendMessage:
    def test_no_token_returns_false(self):
        sender = TelegramSender(bot_token="")
        result = sender.send_message("123", "Hello")
        assert result is False

    @patch("app.alerts.telegram_sender.httpx.post")
    def test_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"ok": True}
        mock_post.return_value = mock_response

        sender = TelegramSender(bot_token="123:ABC")
        result = sender.send_message("456", "Hello")

        assert result is True
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args
        assert "456" in str(call_kwargs)

    @patch("app.alerts.telegram_sender.httpx.post")
    def test_api_error_returns_false(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"ok": False}
        mock_response.text = "Bad Request"
        mock_post.return_value = mock_response

        sender = TelegramSender(bot_token="123:ABC")
        result = sender.send_message("456", "Hello")

        assert result is False

    @patch("app.alerts.telegram_sender.httpx.post")
    def test_exception_returns_false(self, mock_post):
        mock_post.side_effect = Exception("Network error")

        sender = TelegramSender(bot_token="123:ABC")
        result = sender.send_message("456", "Hello")

        assert result is False


class TestSendAlert:
    @patch("app.alerts.telegram_sender.httpx.post")
    def test_formatted_alert(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"ok": True}
        mock_post.return_value = mock_response

        sender = TelegramSender(bot_token="123:ABC")
        result = sender.send_alert(
            chat_id="456",
            account_name="Test Account",
            message="Budget exceeded!",
            severity="critical",
            campaigns=["Campaign 1", "Campaign 2"],
        )

        assert result is True
        call_json = mock_post.call_args[1]["json"]
        text = call_json["text"]
        assert "Test Account" in text
        assert "CRITICAL" in text
        assert "Budget exceeded!" in text
        assert "Campaign 1" in text
        assert "Campaign 2" in text

    @patch("app.alerts.telegram_sender.httpx.post")
    def test_alert_with_many_campaigns_truncates(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"ok": True}
        mock_post.return_value = mock_response

        sender = TelegramSender(bot_token="123:ABC")
        campaigns = [f"Campaign {i}" for i in range(15)]
        result = sender.send_alert(
            chat_id="456",
            account_name="Test",
            message="Alert",
            campaigns=campaigns,
        )

        assert result is True
        text = mock_post.call_args[1]["json"]["text"]
        assert "and 5 more" in text

    def test_no_token_returns_false(self):
        sender = TelegramSender(bot_token="")
        result = sender.send_alert(
            chat_id="456",
            account_name="Test",
            message="Alert",
        )
        assert result is False
