"""Tests for tfais.core.http_utils."""
import pytest
from unittest.mock import patch

from tfais.core.http_utils import retry_request, rate_limit, DEFAULT_HEADERS


def test_default_headers_has_user_agent():
    assert "User-Agent" in DEFAULT_HEADERS
    assert "Mozilla" in DEFAULT_HEADERS["User-Agent"]


def test_retry_request_succeeds_first_try():
    result = retry_request(lambda: 42, max_retries=3)
    assert result == 42


def test_retry_request_succeeds_after_failures():
    call_count = 0

    def flaky():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ConnectionError("transient failure")
        return "success"

    with patch("tfais.core.http_utils.time.sleep"):
        result = retry_request(flaky, max_retries=3, backoff=1)

    assert result == "success"
    assert call_count == 3


def test_retry_request_raises_after_max_retries():
    def always_fails():
        raise ConnectionError("permanent failure")

    with patch("tfais.core.http_utils.time.sleep"):
        with pytest.raises(ConnectionError, match="permanent failure"):
            retry_request(always_fails, max_retries=3, backoff=1)


def test_rate_limit_calls_sleep():
    with patch("tfais.core.http_utils.time.sleep") as mock_sleep:
        rate_limit(1.5)
        mock_sleep.assert_called_once_with(1.5)
