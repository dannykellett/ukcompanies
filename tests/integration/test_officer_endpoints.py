"""Integration tests for officer-related endpoints."""


import httpx
import pytest
import respx

from ukcompanies.client import AsyncClient
from ukcompanies.exceptions import NotFoundError, ValidationError


@pytest.mark.asyncio
class TestOfficersEndpoint:
    """Test the company officers endpoint."""

    @respx.mock
    async def test_get_officers_basic(self):
        """Test getting officers for a company."""
        mock_response = {
            "items": [
                {
                    "name": "John Smith",
                    "officer_id": "abc123",
                    "officer_role": "director",
                    "appointed_on": "2020-01-01",
                    "address": {
                        "address_line_1": "123 Main St",
                        "locality": "London",
                        "postal_code": "SW1A 1AA",
                    },
                },
                {
                    "name": "Jane Doe",
                    "officer_id": "def456",
                    "officer_role": "secretary",
                    "appointed_on": "2020-02-01",
                    "resigned_on": "2021-01-01",
                    "address": {
                        "address_line_1": "456 High St",
                        "locality": "Manchester",
                        "postal_code": "M1 1AA",
                    },
                },
            ],
            "active_count": 1,
            "resigned_count": 1,
            "items_per_page": 35,
            "start_index": 0,
            "total_results": 2,
        }

        route = respx.get("https://api.company-information.service.gov.uk/company/12345678/officers").mock(
            return_value=httpx.Response(
                200,
                json=mock_response,
                headers={
                    "X-Ratelimit-Limit": "600",
                    "X-Ratelimit-Remain": "599",
                    "X-Ratelimit-Reset": "1234567890",
                },
            )
        )

        async with AsyncClient(api_key="test_key") as client:
            result = await client.get_officers("12345678")

        assert route.called
        assert len(result.items) == 2
        assert result.items[0].name == "John Smith"
        assert result.items[0].is_active is True
        assert result.items[1].name == "Jane Doe"
        assert result.items[1].is_active is False
        assert result.active_count == 1
        assert result.resigned_count == 1

    @respx.mock
    async def test_get_officers_with_date_of_birth(self):
        """Test getting officers with privacy-compliant date of birth."""
        mock_response = {
            "items": [
                {
                    "name": "John Smith",
                    "officer_role": "director",
                    "appointed_on": "2020-01-01",
                    "date_of_birth": {
                        "month": 6,
                        "year": 1970,
                    },
                },
            ],
            "items_per_page": 35,
            "start_index": 0,
            "total_results": 1,
        }

        respx.get("https://api.company-information.service.gov.uk/company/12345678/officers").mock(
            return_value=httpx.Response(200, json=mock_response)
        )

        async with AsyncClient(api_key="test_key") as client:
            result = await client.get_officers("12345678")

        assert result.items[0].date_of_birth.month == 6
        assert result.items[0].date_of_birth.year == 1970
        assert str(result.items[0].date_of_birth) == "06/1970"

    @respx.mock
    async def test_get_officers_pagination(self):
        """Test officers endpoint with pagination."""
        mock_response = {
            "items": [{"name": f"Officer {i}", "officer_role": "director"} for i in range(35)],
            "items_per_page": 35,
            "start_index": 0,
            "total_results": 100,
            "links": {
                "self": "/company/12345678/officers",
                "next": "/company/12345678/officers?start_index=35",
            },
        }

        respx.get("https://api.company-information.service.gov.uk/company/12345678/officers").mock(
            return_value=httpx.Response(200, json=mock_response)
        )

        async with AsyncClient(api_key="test_key") as client:
            result = await client.get_officers("12345678")

        assert len(result.items) == 35
        assert result.has_more_pages is True
        assert result.next_start_index == 35

    @respx.mock
    async def test_get_officers_company_not_found(self):
        """Test officers endpoint when company doesn't exist."""
        respx.get("https://api.company-information.service.gov.uk/company/99999999/officers").mock(
            return_value=httpx.Response(404, json={"error": "Company not found"})
        )

        async with AsyncClient(api_key="test_key") as client:
            with pytest.raises(NotFoundError, match="Company not found"):
                await client.get_officers("99999999")

    @respx.mock
    async def test_get_officers_invalid_company_number(self):
        """Test officers endpoint with invalid company number."""
        async with AsyncClient(api_key="test_key") as client:
            with pytest.raises(ValidationError, match="Invalid company number"):
                await client.get_officers("invalid")

    @respx.mock
    async def test_get_officers_with_filters(self):
        """Test officers endpoint with register type and order by filters."""
        respx.get(
            "https://api.company-information.service.gov.uk/company/12345678/officers"
        ).mock(
            return_value=httpx.Response(
                200,
                json={"items": [], "items_per_page": 35, "start_index": 0, "total_results": 0},
            )
        )

        async with AsyncClient(api_key="test_key") as client:
            await client.get_officers(
                "12345678", register_type="directors", order_by="appointed_on"
            )

        # Check the request was made with correct params
        assert respx.calls[0].request.url.params["register_type"] == "directors"
        assert respx.calls[0].request.url.params["order_by"] == "appointed_on"


@pytest.mark.asyncio
class TestAppointmentsEndpoint:
    """Test the officer appointments endpoint."""

    @respx.mock
    async def test_get_appointments_basic(self):
        """Test getting appointments for an officer."""
        mock_response = {
            "items": [
                {
                    "appointed_to": {
                        "company_name": "Test Company Ltd",
                        "company_number": "12345678",
                        "company_status": "active",
                    },
                    "name": "John Smith",
                    "officer_role": "director",
                    "appointed_on": "2020-01-01",
                },
                {
                    "appointed_to": {
                        "company_name": "Another Company Ltd",
                        "company_number": "87654321",
                        "company_status": "dissolved",
                    },
                    "name": "John Smith",
                    "officer_role": "secretary",
                    "appointed_on": "2019-01-01",
                    "resigned_on": "2021-01-01",
                },
            ],
            "items_per_page": 50,
            "start_index": 0,
            "total_results": 2,
            "name": "John Smith",
            "is_corporate_officer": False,
        }

        route = respx.get("https://api.company-information.service.gov.uk/officers/abc123/appointments").mock(
            return_value=httpx.Response(
                200,
                json=mock_response,
                headers={
                    "X-Ratelimit-Limit": "600",
                    "X-Ratelimit-Remain": "598",
                    "X-Ratelimit-Reset": "1234567890",
                },
            )
        )

        async with AsyncClient(api_key="test_key") as client:
            result = await client.get_appointments("abc123")

        assert route.called
        assert len(result.items) == 2
        assert result.items[0].company_name == "Test Company Ltd"
        assert result.items[0].is_active is True
        assert result.items[1].company_name == "Another Company Ltd"
        assert result.items[1].is_active is False
        assert result.name == "John Smith"

    @respx.mock
    async def test_get_appointments_pagination(self):
        """Test appointments endpoint with pagination."""
        mock_response = {
            "items": [
                {
                    "appointed_to": {
                        "company_name": f"Company {i}",
                        "company_number": f"{i:08d}",
                        "company_status": "active",
                    },
                    "name": "John Smith",
                    "officer_role": "director",
                }
                for i in range(50)
            ],
            "items_per_page": 50,
            "start_index": 0,
            "total_results": 150,
        }

        respx.get("https://api.company-information.service.gov.uk/officers/abc123/appointments").mock(
            return_value=httpx.Response(200, json=mock_response)
        )

        async with AsyncClient(api_key="test_key") as client:
            result = await client.get_appointments("abc123")

        assert len(result.items) == 50
        assert result.has_more_pages is True
        assert result.next_start_index == 50

    @respx.mock
    async def test_get_appointments_pages_generator(self):
        """Test paginated appointments generator."""
        # First page
        page1 = {
            "items": [
                {
                    "appointed_to": {"company_name": f"Company {i}", "company_number": f"{i:08d}"},
                    "name": "John Smith",
                    "officer_role": "director",
                }
                for i in range(2)
            ],
            "items_per_page": 2,
            "start_index": 0,
            "total_results": 5,
        }

        # Second page
        page2 = {
            "items": [
                {
                    "appointed_to": {"company_name": f"Company {i}", "company_number": f"{i:08d}"},
                    "name": "John Smith",
                    "officer_role": "director",
                }
                for i in range(2, 4)
            ],
            "items_per_page": 2,
            "start_index": 2,
            "total_results": 5,
        }

        # Third page (last)
        page3 = {
            "items": [
                {
                    "appointed_to": {"company_name": "Company 4", "company_number": "00000004"},
                    "name": "John Smith",
                    "officer_role": "director",
                }
            ],
            "items_per_page": 2,
            "start_index": 4,
            "total_results": 5,
        }

        route = respx.get("https://api.company-information.service.gov.uk/officers/abc123/appointments")
        route.side_effect = [
            httpx.Response(200, json=page1),
            httpx.Response(200, json=page2),
            httpx.Response(200, json=page3),
        ]

        async with AsyncClient(api_key="test_key") as client:
            pages = []
            async for page in client.get_appointments_pages("abc123", per_page=2):
                pages.append(page)

        assert len(pages) == 3
        assert len(pages[0].items) == 2
        assert len(pages[1].items) == 2
        assert len(pages[2].items) == 1
        assert route.call_count == 3

    @respx.mock
    async def test_get_appointments_officer_not_found(self):
        """Test appointments endpoint when officer doesn't exist."""
        respx.get("https://api.company-information.service.gov.uk/officers/invalid/appointments").mock(
            return_value=httpx.Response(404, json={"error": "Officer not found"})
        )

        async with AsyncClient(api_key="test_key") as client:
            with pytest.raises(NotFoundError, match="Officer not found"):
                await client.get_appointments("invalid")

    @respx.mock
    async def test_get_appointments_empty_officer_id(self):
        """Test appointments endpoint with empty officer ID."""
        async with AsyncClient(api_key="test_key") as client:
            with pytest.raises(ValidationError, match="Officer ID cannot be empty"):
                await client.get_appointments("")


@pytest.mark.asyncio
class TestDisqualifiedOfficersEndpoint:
    """Test the disqualified officers endpoints."""

    @respx.mock
    async def test_get_disqualified_natural(self):
        """Test getting disqualification for natural person."""
        mock_response = {
            "items": [
                {
                    "forename": "John",
                    "surname": "Smith",
                    "title": "Mr",
                    "date_of_birth": "1970",
                    "disqualifications": [
                        {
                            "disqualified_from": "2020-01-01",
                            "disqualified_until": "2025-01-01",
                            "reason": {
                                "description_identifier": "misconduct",
                                "act": "company-directors-disqualification-act-1986",
                                "description": "Misconduct in connection with company",
                            },
                            "court_name": "High Court",
                            "court_order_date": "2019-12-01",
                        }
                    ],
                }
            ],
            "items_per_page": 50,
            "start_index": 0,
            "total_results": 1,
        }

        route = respx.get(
            "https://api.company-information.service.gov.uk/disqualified-officers/natural/abc123"
        ).mock(
            return_value=httpx.Response(
                200,
                json=mock_response,
                headers={
                    "X-Ratelimit-Limit": "600",
                    "X-Ratelimit-Remain": "597",
                    "X-Ratelimit-Reset": "1234567890",
                },
            )
        )

        async with AsyncClient(api_key="test_key") as client:
            result = await client.get_disqualified_natural("abc123")

        assert route.called
        assert len(result.items) == 1
        assert result.items[0].forename == "John"
        assert result.items[0].surname == "Smith"
        assert len(result.items[0].disqualifications) == 1
        assert result.items[0].disqualifications[0].court_name == "High Court"

    @respx.mock
    async def test_get_disqualified_corporate(self):
        """Test getting disqualification for corporate officer."""
        mock_response = {
            "items": [
                {
                    "company_name": "Corporate Officer Ltd",
                    "company_number": "12345678",
                    "disqualifications": [
                        {
                            "disqualified_from": "2020-01-01",
                            "disqualified_until": "2025-01-01",
                            "undertaken_on": "2019-12-15",
                            "is_undertaking": True,
                        }
                    ],
                }
            ],
            "items_per_page": 50,
            "start_index": 0,
            "total_results": 1,
        }

        route = respx.get(
            "https://api.company-information.service.gov.uk/disqualified-officers/corporate/corp123"
        ).mock(return_value=httpx.Response(200, json=mock_response))

        async with AsyncClient(api_key="test_key") as client:
            result = await client.get_disqualified_corporate("corp123")

        assert route.called
        assert len(result.items) == 1
        assert result.items[0].disqualifications[0].is_undertaking is True

    @respx.mock
    async def test_disqualified_convenience_method_natural(self):
        """Test convenience method for natural disqualification."""
        mock_response = {"items": [], "items_per_page": 50, "start_index": 0, "total_results": 0}

        respx.get(
            "https://api.company-information.service.gov.uk/disqualified-officers/natural/abc123"
        ).mock(return_value=httpx.Response(200, json=mock_response))

        async with AsyncClient(api_key="test_key") as client:
            result = await client.disqualified("abc123", corporate=False)

        assert result.items == []

    @respx.mock
    async def test_disqualified_convenience_method_corporate(self):
        """Test convenience method for corporate disqualification."""
        mock_response = {"items": [], "items_per_page": 50, "start_index": 0, "total_results": 0}

        respx.get(
            "https://api.company-information.service.gov.uk/disqualified-officers/corporate/corp123"
        ).mock(return_value=httpx.Response(200, json=mock_response))

        async with AsyncClient(api_key="test_key") as client:
            result = await client.disqualified("corp123", corporate=True)

        assert result.items == []

    @respx.mock
    async def test_get_disqualified_not_found(self):
        """Test disqualified endpoint when officer has no disqualifications."""
        respx.get(
            "https://api.company-information.service.gov.uk/disqualified-officers/natural/nodisq"
        ).mock(return_value=httpx.Response(404, json={"error": "No disqualifications found"}))

        async with AsyncClient(api_key="test_key") as client:
            with pytest.raises(NotFoundError, match="No disqualifications found"):
                await client.get_disqualified_natural("nodisq")

    @respx.mock
    async def test_get_disqualified_empty_officer_id(self):
        """Test disqualified endpoint with empty officer ID."""
        async with AsyncClient(api_key="test_key") as client:
            with pytest.raises(ValidationError, match="Officer ID cannot be empty"):
                await client.get_disqualified_natural("")


@pytest.mark.asyncio
class TestPrivacyCompliance:
    """Test privacy compliance for date of birth handling."""

    @respx.mock
    async def test_date_of_birth_privacy(self):
        """Test that date of birth only includes month and year."""
        mock_response = {
            "items": [
                {
                    "name": "John Smith",
                    "officer_role": "director",
                    "date_of_birth": {
                        "month": 6,
                        "year": 1970,
                        # API should never return day, but if it does, our model shouldn't accept it
                    },
                }
            ],
            "items_per_page": 35,
            "start_index": 0,
            "total_results": 1,
        }

        respx.get("https://api.company-information.service.gov.uk/company/12345678/officers").mock(
            return_value=httpx.Response(200, json=mock_response)
        )

        async with AsyncClient(api_key="test_key") as client:
            result = await client.get_officers("12345678")

        # Verify we only have month and year
        dob = result.items[0].date_of_birth
        assert hasattr(dob, "month")
        assert hasattr(dob, "year")
        assert not hasattr(dob, "day")

        # Verify string representation doesn't include day
        assert "/" in str(dob)
        parts = str(dob).split("/")
        assert len(parts) == 2  # Only MM/YYYY
