"""Integration tests for search endpoints."""


import httpx
import pytest
import respx

from ukcompanies import AsyncClient
from ukcompanies.models.search import CompanySearchResult, OfficerSearchResult


@pytest.mark.asyncio
class TestSearchCompanies:
    """Test search_companies endpoint."""

    @respx.mock
    async def test_search_companies_success(self):
        """Test successful company search."""
        mock_response = {
            "items": [
                {
                    "company_number": "12345678",
                    "title": "TEST COMPANY LTD",
                    "company_type": "ltd",
                    "company_status": "active",
                    "date_of_creation": "2020-01-01",
                    "address_snippet": "123 Test Street, London, SW1A 1AA",
                }
            ],
            "items_per_page": 20,
            "kind": "search#companies",
            "page_number": 1,
            "start_index": 0,
            "total_results": 1,
        }

        route = respx.get("https://api.company-information.service.gov.uk/search/companies").mock(
            return_value=httpx.Response(200, json=mock_response)
        )

        async with AsyncClient(api_key="test-key") as client:
            result = await client.search_companies("test company")

        assert isinstance(result, CompanySearchResult)
        assert len(result.items) == 1
        assert result.items[0].company_number == "12345678"
        assert result.items[0].title == "TEST COMPANY LTD"
        assert result.total_results == 1
        assert route.called

    @respx.mock
    async def test_search_companies_with_pagination(self):
        """Test company search with pagination parameters."""
        mock_response = {
            "items": [],
            "items_per_page": 50,
            "kind": "search#companies",
            "page_number": 2,
            "start_index": 50,
            "total_results": 100,
        }

        route = respx.get("https://api.company-information.service.gov.uk/search/companies").mock(
            return_value=httpx.Response(200, json=mock_response)
        )

        async with AsyncClient(api_key="test-key") as client:
            result = await client.search_companies("test", items_per_page=50, start_index=50)

        assert result.items_per_page == 50
        assert result.start_index == 50
        assert result.total_results == 100
        assert result.has_more_pages is False  # 50 + 50 = 100, no more pages

        # Check query parameters were passed correctly
        assert route.call_count == 1
        request = route.calls[0].request
        assert request.url.params["q"] == "test"
        assert request.url.params["items_per_page"] == "50"
        assert request.url.params["start_index"] == "50"

    @respx.mock
    async def test_search_companies_empty_results(self):
        """Test company search with no results."""
        mock_response = {
            "items": [],
            "items_per_page": 20,
            "kind": "search#companies",
            "page_number": 1,
            "start_index": 0,
            "total_results": 0,
        }

        respx.get("https://api.company-information.service.gov.uk/search/companies").mock(
            return_value=httpx.Response(200, json=mock_response)
        )

        async with AsyncClient(api_key="test-key") as client:
            result = await client.search_companies("nonexistent company xyz")

        assert len(result.items) == 0
        assert result.total_results == 0
        assert result.has_more_pages is False


@pytest.mark.asyncio
class TestSearchOfficers:
    """Test search_officers endpoint."""

    @respx.mock
    async def test_search_officers_success(self):
        """Test successful officer search."""
        mock_response = {
            "items": [
                {
                    "title": "John SMITH",
                    "description": "Director",
                    "appointment_count": 5,
                    "date_of_birth": {"month": 1, "year": 1980},
                    "address_snippet": "123 Test Street, London",
                }
            ],
            "items_per_page": 20,
            "kind": "search#officers",
            "page_number": 1,
            "start_index": 0,
            "total_results": 1,
        }

        route = respx.get("https://api.company-information.service.gov.uk/search/officers").mock(
            return_value=httpx.Response(200, json=mock_response)
        )

        async with AsyncClient(api_key="test-key") as client:
            result = await client.search_officers("john smith")

        assert isinstance(result, OfficerSearchResult)
        assert len(result.items) == 1
        assert result.items[0].title == "John SMITH"
        assert result.items[0].description == "Director"
        assert result.items[0].appointment_count == 5
        assert route.called


@pytest.mark.asyncio
class TestSearchAll:
    """Test search_all endpoint."""

    @respx.mock
    async def test_search_all_mixed_results(self):
        """Test search all with mixed result types."""
        mock_response = {
            "items": [
                {
                    "kind": "searchresults#company",
                    "company_number": "12345678",
                    "title": "TEST COMPANY LTD",
                    "company_type": "ltd",
                    "company_status": "active",
                },
                {
                    "kind": "searchresults#officer",
                    "title": "John SMITH",
                    "description": "Director",
                    "appointment_count": 3,
                },
            ],
            "items_per_page": 20,
            "kind": "search#all",
            "page_number": 1,
            "start_index": 0,
            "total_results": 2,
        }

        respx.get("https://api.company-information.service.gov.uk/search").mock(
            return_value=httpx.Response(200, json=mock_response)
        )

        async with AsyncClient(api_key="test-key") as client:
            result = await client.search_all("test")

        assert len(result.items) == 2
        # Note: The actual discrimination between types would need to be handled
        # by the API response parsing logic

    @respx.mock
    async def test_search_all_pages_generator(self):
        """Test search_all_pages async generator."""
        # First page
        mock_response_1 = {
            "items": [{"title": "Item 1"}],
            "items_per_page": 1,
            "kind": "search#all",
            "page_number": 1,
            "start_index": 0,
            "total_results": 2,
        }

        # Second page
        mock_response_2 = {
            "items": [{"title": "Item 2"}],
            "items_per_page": 1,
            "kind": "search#all",
            "page_number": 2,
            "start_index": 1,
            "total_results": 2,
        }

        route = respx.get("https://api.company-information.service.gov.uk/search")
        route.side_effect = [
            httpx.Response(200, json=mock_response_1),
            httpx.Response(200, json=mock_response_2),
        ]

        async with AsyncClient(api_key="test-key") as client:
            pages = []
            async for page in client.search_all_pages("test", per_page=1):
                pages.append(page)

        assert len(pages) == 2
        # Items are raw dicts in AllSearchResult since they don't have a kind field
        # to discriminate the type
        assert len(pages[0].items) == 1
        assert len(pages[1].items) == 1

    @respx.mock
    async def test_search_all_pages_with_max_pages(self):
        """Test search_all_pages with max_pages limit."""
        mock_response = {
            "items": [{"title": f"Item {i}"} for i in range(10)],
            "items_per_page": 10,
            "kind": "search#all",
            "page_number": 1,
            "start_index": 0,
            "total_results": 100,  # 10 pages total
        }

        respx.get("https://api.company-information.service.gov.uk/search").mock(
            return_value=httpx.Response(200, json=mock_response)
        )

        async with AsyncClient(api_key="test-key") as client:
            pages = []
            async for page in client.search_all_pages("test", per_page=10, max_pages=2):
                pages.append(page)

        # Should stop after 2 pages even though more are available
        assert len(pages) == 2
