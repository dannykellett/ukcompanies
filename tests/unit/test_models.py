"""Unit tests for models."""

from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from ukcompanies.models import Address, BaseModel, RateLimitInfo


class TestBaseModel:
    """Test base model functionality."""

    def test_to_dict(self):
        """Test converting model to dictionary."""
        model = BaseModel()
        result = model.to_dict()
        assert isinstance(result, dict)

    def test_to_dict_exclude_none(self):
        """Test excluding None values from dict."""
        # Create a test model with optional fields
        class TestModel(BaseModel):
            required: str = "value"
            optional: str = None

        model = TestModel(required="test")

        # With exclude_none=True (default)
        result = model.to_dict(exclude_none=True)
        assert "required" in result
        assert "optional" not in result

        # With exclude_none=False
        result = model.to_dict(exclude_none=False)
        assert "required" in result
        assert "optional" in result
        assert result["optional"] is None

    def test_to_json(self):
        """Test converting model to JSON string."""
        model = BaseModel()
        result = model.to_json()
        assert isinstance(result, str)
        assert "{" in result  # Valid JSON

    def test_extra_fields_forbidden(self):
        """Test that extra fields are not allowed."""
        with pytest.raises(ValidationError) as exc_info:
            BaseModel(extra_field="not_allowed")
        assert "extra" in str(exc_info.value).lower()


class TestAddress:
    """Test Address model."""

    def test_minimal_address(self):
        """Test creating address with minimal fields."""
        address = Address(address_line_1="123 Main St")
        assert address.address_line_1 == "123 Main St"
        assert address.premises is None
        assert address.address_line_2 is None
        assert address.locality is None
        assert address.region is None
        assert address.postal_code is None
        assert address.country is None

    def test_full_address(self):
        """Test creating address with all fields."""
        address = Address(
            premises="Unit 5",
            address_line_1="123 Main St",
            address_line_2="Business Park",
            locality="London",
            region="Greater London",
            postal_code="SW1A 1AA",
            country="United Kingdom"
        )
        assert address.premises == "Unit 5"
        assert address.address_line_1 == "123 Main St"
        assert address.address_line_2 == "Business Park"
        assert address.locality == "London"
        assert address.region == "Greater London"
        assert address.postal_code == "SW1A 1AA"
        assert address.country == "United Kingdom"

    def test_full_address_property(self):
        """Test full_address property formatting."""
        # Minimal address
        address = Address(address_line_1="123 Main St")
        assert address.full_address == "123 Main St"

        # Full address
        address = Address(
            premises="Unit 5",
            address_line_1="123 Main St",
            address_line_2="Business Park",
            locality="London",
            region="Greater London",
            postal_code="SW1A 1AA",
            country="United Kingdom"
        )
        expected = (
            "Unit 5, 123 Main St, Business Park, London, Greater London, "
            "SW1A 1AA, United Kingdom"
        )
        assert address.full_address == expected

        # Partial address
        address = Address(
            address_line_1="123 Main St",
            locality="London",
            postal_code="SW1A 1AA"
        )
        assert address.full_address == "123 Main St, London, SW1A 1AA"

    def test_missing_required_field(self):
        """Test that address_line_1 is required."""
        with pytest.raises(ValidationError) as exc_info:
            Address()
        assert "address_line_1" in str(exc_info.value)

    def test_whitespace_stripping(self):
        """Test that whitespace is stripped from fields."""
        address = Address(
            address_line_1="  123 Main St  ",
            locality="  London  "
        )
        assert address.address_line_1 == "123 Main St"
        assert address.locality == "London"


class TestRateLimitInfo:
    """Test RateLimitInfo model."""

    def test_basic_rate_limit(self):
        """Test creating rate limit info."""
        reset_time = datetime.now(timezone.utc) + timedelta(minutes=5)
        info = RateLimitInfo(
            remain=450,
            limit=600,
            reset=reset_time
        )
        assert info.remain == 450
        assert info.limit == 600
        assert info.reset == reset_time
        assert info.retry_after is None

    def test_with_retry_after(self):
        """Test rate limit with retry_after."""
        reset_time = datetime.now(timezone.utc) + timedelta(minutes=5)
        info = RateLimitInfo(
            remain=0,
            limit=600,
            reset=reset_time,
            retry_after=60
        )
        assert info.remain == 0
        assert info.retry_after == 60

    def test_is_limited_property(self):
        """Test is_limited property."""
        reset_time = datetime.now(timezone.utc) + timedelta(minutes=5)

        # Not limited
        info = RateLimitInfo(remain=100, limit=600, reset=reset_time)
        assert info.is_limited is False

        # Limited (no remaining)
        info = RateLimitInfo(remain=0, limit=600, reset=reset_time)
        assert info.is_limited is True

    def test_percent_remaining_property(self):
        """Test percent_remaining calculation."""
        reset_time = datetime.now(timezone.utc) + timedelta(minutes=5)

        # 50% remaining
        info = RateLimitInfo(remain=300, limit=600, reset=reset_time)
        assert info.percent_remaining == 50.0

        # 100% remaining
        info = RateLimitInfo(remain=600, limit=600, reset=reset_time)
        assert info.percent_remaining == 100.0

        # 0% remaining
        info = RateLimitInfo(remain=0, limit=600, reset=reset_time)
        assert info.percent_remaining == 0.0

        # Edge case: limit is 0
        info = RateLimitInfo(remain=0, limit=0, reset=reset_time)
        assert info.percent_remaining == 0.0

    def test_seconds_until_reset_property(self):
        """Test seconds_until_reset calculation."""
        # Reset in future
        reset_time = datetime.now(timezone.utc) + timedelta(minutes=5)
        info = RateLimitInfo(remain=100, limit=600, reset=reset_time)
        seconds = info.seconds_until_reset
        assert 295 < seconds < 305  # Around 5 minutes

        # Reset in past
        reset_time = datetime.now(timezone.utc) - timedelta(minutes=5)
        info = RateLimitInfo(remain=600, limit=600, reset=reset_time)
        seconds = info.seconds_until_reset
        assert seconds < 0  # Negative value

    def test_missing_required_fields(self):
        """Test that all required fields must be provided."""
        with pytest.raises(ValidationError) as exc_info:
            RateLimitInfo()
        error_str = str(exc_info.value)
        assert "remain" in error_str
        assert "limit" in error_str
        assert "reset" in error_str
