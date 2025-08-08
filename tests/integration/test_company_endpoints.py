"""Integration tests for company endpoints."""

from datetime import date

import httpx
import pytest
import respx

from ukcompanies import AsyncClient
from ukcompanies.exceptions import NotFoundError, ValidationError
from ukcompanies.models import Address, Company


@pytest.mark.asyncio
class TestGetCompany:
    """Test get_company (profile) endpoint."""

    @respx.mock
    async def test_get_company_success(self):
        """Test successful company profile retrieval."""
        mock_response = {
            "company_number": "12345678",
            "company_name": "TEST COMPANY LIMITED",
            "company_status": "active",
            "date_of_creation": "2020-01-01",
            "type": "ltd",
            "jurisdiction": "england-wales",
            "sic_codes": ["62012", "62020"],
            "registered_office_address": {
                "address_line_1": "123 Test Street",
                "locality": "London",
                "postal_code": "SW1A 1AA",
                "country": "United Kingdom",
            },
            "accounts": {
                "accounting_reference_date": {"day": 31, "month": 12},
                "next_due": "2025-09-30",
            },
            "confirmation_statement": {
                "next_due": "2025-01-31",
                "overdue": False,
            },
            "has_been_liquidated": False,
            "has_insolvency_history": False,
            "can_file": True,
        }

        route = respx.get("https://api.company-information.service.gov.uk/company/12345678").mock(
            return_value=httpx.Response(200, json=mock_response)
        )

        async with AsyncClient(api_key="test-key") as client:
            company = await client.get_company("12345678")

        assert isinstance(company, Company)
        assert company.company_number == "12345678"
        assert company.company_name == "TEST COMPANY LIMITED"
        assert company.company_status == "active"
        assert company.is_active is True
        assert company.date_of_creation == date(2020, 1, 1)
        assert company.type == "ltd"
        assert company.jurisdiction == "england-wales"
        assert company.sic_codes == ["62012", "62020"]
        assert company.registered_office_address.address_line_1 == "123 Test Street"
        assert company.accounts.accounting_reference_date.day == 31
        assert company.confirmation_statement.next_due == date(2025, 1, 31)
        assert route.called

    @respx.mock
    async def test_get_company_normalizes_number(self):
        """Test that company number is normalized before request."""
        mock_response = {
            "company_number": "01234567",
            "company_name": "TEST COMPANY",
        }

        route = respx.get("https://api.company-information.service.gov.uk/company/01234567").mock(
            return_value=httpx.Response(200, json=mock_response)
        )

        async with AsyncClient(api_key="test-key") as client:
            # Pass in 7-digit number, should be padded to 8
            company = await client.get_company("1234567")

        assert company.company_number == "01234567"
        assert route.called

    @respx.mock
    async def test_get_company_not_found(self):
        """Test 404 error when company not found."""
        respx.get("https://api.company-information.service.gov.uk/company/99999999").mock(
            return_value=httpx.Response(404, json={"error": "Company not found"})
        )

        async with AsyncClient(api_key="test-key") as client:
            with pytest.raises(NotFoundError) as exc_info:
                await client.get_company("99999999")
            assert "not found" in str(exc_info.value).lower()

    async def test_get_company_invalid_number(self):
        """Test validation error for invalid company number."""
        async with AsyncClient(api_key="test-key") as client:
            with pytest.raises(ValidationError) as exc_info:
                await client.get_company("INVALID")
            assert "Must be 8 characters" in str(exc_info.value)

    @respx.mock
    async def test_profile_alias(self):
        """Test that profile() is an alias for get_company()."""
        mock_response = {
            "company_number": "12345678",
            "company_name": "TEST COMPANY",
        }

        respx.get("https://api.company-information.service.gov.uk/company/12345678").mock(
            return_value=httpx.Response(200, json=mock_response)
        )

        async with AsyncClient(api_key="test-key") as client:
            company = await client.profile("12345678")

        assert company.company_number == "12345678"
        assert company.company_name == "TEST COMPANY"


@pytest.mark.asyncio
class TestGetCompanyAddress:
    """Test get_company_address endpoint."""

    @respx.mock
    async def test_get_company_address_success(self):
        """Test successful company address retrieval."""
        mock_response = {
            "premises": "Unit 5",
            "address_line_1": "123 Test Street",
            "address_line_2": "Test Business Park",
            "locality": "London",
            "region": "Greater London",
            "postal_code": "SW1A 1AA",
            "country": "United Kingdom",
        }

        route = respx.get(
            "https://api.company-information.service.gov.uk/company/12345678/registered-office-address"
        ).mock(return_value=httpx.Response(200, json=mock_response))

        async with AsyncClient(api_key="test-key") as client:
            address = await client.get_company_address("12345678")

        assert isinstance(address, Address)
        assert address.premises == "Unit 5"
        assert address.address_line_1 == "123 Test Street"
        assert address.address_line_2 == "Test Business Park"
        assert address.locality == "London"
        assert address.region == "Greater London"
        assert address.postal_code == "SW1A 1AA"
        assert address.country == "United Kingdom"
        assert route.called

    @respx.mock
    async def test_get_company_address_minimal(self):
        """Test company address with minimal fields."""
        mock_response = {
            "address_line_1": "123 Test Street",
            "postal_code": "SW1A 1AA",
        }

        respx.get(
            "https://api.company-information.service.gov.uk/company/12345678/registered-office-address"
        ).mock(return_value=httpx.Response(200, json=mock_response))

        async with AsyncClient(api_key="test-key") as client:
            address = await client.get_company_address("12345678")

        assert address.address_line_1 == "123 Test Street"
        assert address.postal_code == "SW1A 1AA"
        assert address.premises is None
        assert address.locality is None

    @respx.mock
    async def test_get_company_address_not_found(self):
        """Test 404 error when company address not found."""
        respx.get(
            "https://api.company-information.service.gov.uk/company/99999999/registered-office-address"
        ).mock(return_value=httpx.Response(404, json={"error": "Company not found"}))

        async with AsyncClient(api_key="test-key") as client:
            with pytest.raises(NotFoundError) as exc_info:
                await client.get_company_address("99999999")
            assert "not found" in str(exc_info.value).lower()

    @respx.mock
    async def test_address_alias(self):
        """Test that address() is an alias for get_company_address()."""
        mock_response = {
            "address_line_1": "123 Test Street",
            "postal_code": "SW1A 1AA",
        }

        respx.get(
            "https://api.company-information.service.gov.uk/company/12345678/registered-office-address"
        ).mock(return_value=httpx.Response(200, json=mock_response))

        async with AsyncClient(api_key="test-key") as client:
            address = await client.address("12345678")

        assert address.address_line_1 == "123 Test Street"
        assert address.postal_code == "SW1A 1AA"
