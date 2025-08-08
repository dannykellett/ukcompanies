"""Unit tests for AsyncClient."""

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import httpx
import pytest
import respx

from ukcompanies.client import AsyncClient
from ukcompanies.config import Config
from ukcompanies.exceptions import (
    AuthenticationError,
    NetworkError,
    NotFoundError,
    RateLimitError,
    ServerError,
    ValidationError,
)


@pytest.mark.asyncio
class TestAsyncClient:
    """Test AsyncClient class."""

    async def test_init_with_api_key(self):
        """Test client initialization with API key."""
        client = AsyncClient(api_key="test-api-key-12345678901234567890")
        assert client.config.api_key == "test-api-key-12345678901234567890"
        assert client.auth.api_key == "test-api-key-12345678901234567890"

    async def test_init_with_config(self):
        """Test client initialization with Config object."""
        config = Config(api_key="test-api-key-12345678901234567890", timeout=45.0)
        client = AsyncClient(config=config)
        assert client.config.api_key == "test-api-key-12345678901234567890"
        assert client.config.timeout == 45.0

    async def test_init_with_config_and_api_key_override(self):
        """Test that api_key parameter overrides config."""
        config = Config(api_key="config-key-12345678901234567890")
        client = AsyncClient(api_key="override-key-12345678901234567890", config=config)
        assert client.config.api_key == "override-key-12345678901234567890"

    async def test_init_with_kwargs(self):
        """Test client initialization with kwargs."""
        client = AsyncClient(
            api_key="test-api-key-12345678901234567890",
            timeout=60.0,
            use_sandbox=True
        )
        assert client.config.timeout == 60.0
        assert client.config.use_sandbox is True

    @patch.dict("os.environ", {"COMPANIES_HOUSE_API_KEY": "env-key-12345678901234567890"})
    async def test_init_from_environment(self):
        """Test client initialization from environment."""
        client = AsyncClient()
        assert client.config.api_key == "env-key-12345678901234567890"

    async def test_context_manager(self):
        """Test client as async context manager."""
        client = AsyncClient(api_key="test-api-key-12345678901234567890")

        # Client should not be initialized yet
        assert client._client is None

        async with client:
            # Client should be initialized
            assert client._client is not None
            assert isinstance(client._client, httpx.AsyncClient)

        # Client should be closed
        # Note: We can't directly check if closed, but we can verify it was set
        assert client._client is not None

    async def test_validate_company_number_valid(self):
        """Test company number validation with valid numbers."""
        client = AsyncClient(api_key="test-key")

        # 8-character alphanumeric
        assert client.validate_company_number("12345678") == "12345678"
        assert client.validate_company_number("AB123456") == "AB123456"

        # 7-digit numeric (padded)
        assert client.validate_company_number("1234567") == "01234567"

        # With spaces (removed)
        assert client.validate_company_number("12 34 56 78") == "12345678"

        # Lowercase (converted)
        assert client.validate_company_number("ab123456") == "AB123456"

    async def test_validate_company_number_invalid(self):
        """Test company number validation with invalid numbers."""
        client = AsyncClient(api_key="test-key")

        # Empty
        with pytest.raises(ValidationError) as exc_info:
            client.validate_company_number("")
        assert "cannot be empty" in str(exc_info.value)

        # Too short
        with pytest.raises(ValidationError) as exc_info:
            client.validate_company_number("123")
        assert "Invalid company number format" in str(exc_info.value)

        # Too long
        with pytest.raises(ValidationError) as exc_info:
            client.validate_company_number("123456789")
        assert "Invalid company number format" in str(exc_info.value)

        # Invalid characters
        with pytest.raises(ValidationError) as exc_info:
            client.validate_company_number("12-34-56")
        assert "Invalid company number format" in str(exc_info.value)

    async def test_extract_rate_limit_info(self):
        """Test extracting rate limit info from headers."""
        client = AsyncClient(api_key="test-key")

        # Create mock response with rate limit headers
        reset_time = int((datetime.now(timezone.utc) + timedelta(minutes=5)).timestamp())
        response = MagicMock()
        response.headers = {
            "X-Ratelimit-Remain": "450",
            "X-Ratelimit-Limit": "600",
            "X-Ratelimit-Reset": str(reset_time),
            "Retry-After": "60"
        }

        info = client._extract_rate_limit_info(response)

        assert info is not None
        assert info.remain == 450
        assert info.limit == 600
        assert info.retry_after == 60
        assert client.rate_limit_info == info  # Should be stored

    async def test_extract_rate_limit_info_missing_headers(self):
        """Test extraction when headers are missing."""
        client = AsyncClient(api_key="test-key")

        response = MagicMock()
        response.headers = {}

        info = client._extract_rate_limit_info(response)
        assert info is None

    async def test_extract_rate_limit_info_invalid_values(self):
        """Test extraction with invalid header values."""
        client = AsyncClient(api_key="test-key")

        response = MagicMock()
        response.headers = {
            "X-Ratelimit-Remain": "invalid",
            "X-Ratelimit-Limit": "600",
            "X-Ratelimit-Reset": "not-a-timestamp"
        }

        info = client._extract_rate_limit_info(response)
        assert info is None

    async def test_handle_error_response_401(self):
        """Test handling 401 authentication error."""
        client = AsyncClient(api_key="test-key")

        response = MagicMock()
        response.status_code = 401
        response.json.return_value = {"error": "Invalid API key"}

        with pytest.raises(AuthenticationError) as exc_info:
            client._handle_error_response(response)
        assert "Invalid API key" in str(exc_info.value)

    async def test_handle_error_response_404(self):
        """Test handling 404 not found error."""
        client = AsyncClient(api_key="test-key")

        response = MagicMock()
        response.status_code = 404
        response.text = "Company not found"
        response.json.side_effect = Exception()  # JSON parsing fails

        with pytest.raises(NotFoundError) as exc_info:
            client._handle_error_response(response)
        assert "Company not found" in str(exc_info.value)

    async def test_handle_error_response_429(self):
        """Test handling 429 rate limit error."""
        from datetime import datetime, timezone
        client = AsyncClient(api_key="test-key")

        # Create a future timestamp for rate limit reset
        future_timestamp = int(datetime.now(timezone.utc).timestamp()) + 60

        response = MagicMock()
        response.status_code = 429
        response.headers = {
            "X-Ratelimit-Remain": "0",
            "X-Ratelimit-Limit": "600",
            "X-Ratelimit-Reset": str(future_timestamp)
        }
        response.json.return_value = {"error": "Rate limit exceeded"}

        with pytest.raises(RateLimitError) as exc_info:
            client._handle_error_response(response)

        error = exc_info.value
        assert "Rate limit exceeded" in str(error)
        assert error.rate_limit_remain == 0
        assert error.rate_limit_limit == 600
        assert error.rate_limit_reset is not None
        assert error.retry_after is not None  # Should be calculated from reset time
        assert 59 <= error.retry_after <= 61  # Allow for small timing differences

    async def test_handle_error_response_400(self):
        """Test handling 400 validation error."""
        client = AsyncClient(api_key="test-key")

        response = MagicMock()
        response.status_code = 400
        response.json.return_value = {"error": "Invalid request"}

        with pytest.raises(ValidationError) as exc_info:
            client._handle_error_response(response)
        assert "Invalid request" in str(exc_info.value)

    async def test_handle_error_response_500(self):
        """Test handling 500 server error."""
        client = AsyncClient(api_key="test-key")

        response = MagicMock()
        response.status_code = 500
        response.text = "Internal server error"
        response.json.side_effect = Exception()

        with pytest.raises(ServerError) as exc_info:
            client._handle_error_response(response)
        assert "Internal server error" in str(exc_info.value)
        assert exc_info.value.status_code == 500

    @respx.mock
    async def test_request_success(self):
        """Test successful request."""
        # Mock successful response
        respx.get("https://api.company-information.service.gov.uk/test").mock(
            return_value=httpx.Response(
                200,
                json={"result": "success"},
                headers={
                    "X-Ratelimit-Remain": "599",
                    "X-Ratelimit-Limit": "600",
                    "X-Ratelimit-Reset": str(int(datetime.now(timezone.utc).timestamp()))
                }
            )
        )

        async with AsyncClient(api_key="test-key") as client:
            response = await client._request("GET", "/test")
            assert response.status_code == 200
            assert client.rate_limit_info is not None
            assert client.rate_limit_info.remain == 599

    @respx.mock
    async def test_request_network_error(self):
        """Test request with network error."""
        # Mock network error
        respx.get("https://api.company-information.service.gov.uk/test").mock(
            side_effect=httpx.NetworkError("Connection failed")
        )

        async with AsyncClient(api_key="test-key") as client:
            with pytest.raises(NetworkError) as exc_info:
                await client._request("GET", "/test")
            assert "Connection failed" in str(exc_info.value)

    @respx.mock
    async def test_request_timeout(self):
        """Test request timeout."""
        # Mock timeout
        respx.get("https://api.company-information.service.gov.uk/test").mock(
            side_effect=httpx.TimeoutException("Request timeout")
        )

        async with AsyncClient(api_key="test-key") as client:
            with pytest.raises(NetworkError) as exc_info:
                await client._request("GET", "/test")
            assert "Request timeout" in str(exc_info.value)

    async def test_request_without_context_manager(self):
        """Test that request fails without context manager."""
        client = AsyncClient(api_key="test-key")

        with pytest.raises(RuntimeError) as exc_info:
            await client._request("GET", "/test")
        assert "not initialized" in str(exc_info.value)

    @respx.mock
    async def test_get_method(self):
        """Test GET method."""
        respx.get("https://api.company-information.service.gov.uk/test").mock(
            return_value=httpx.Response(200, json={"data": "test"})
        )

        async with AsyncClient(api_key="test-key") as client:
            result = await client.get("/test")
            assert result == {"data": "test"}

    @respx.mock
    async def test_get_method_with_params(self):
        """Test GET method with query parameters."""
        respx.get("https://api.company-information.service.gov.uk/test?q=search").mock(
            return_value=httpx.Response(200, json={"results": []})
        )

        async with AsyncClient(api_key="test-key") as client:
            result = await client.get("/test", params={"q": "search"})
            assert result == {"results": []}

    @respx.mock
    async def test_post_method(self):
        """Test POST method."""
        respx.post("https://api.company-information.service.gov.uk/test").mock(
            return_value=httpx.Response(201, json={"created": True})
        )

        async with AsyncClient(api_key="test-key") as client:
            result = await client.post("/test", json={"name": "test"})
            assert result == {"created": True}
