"""Integration tests for filing history endpoints."""

from datetime import date

import pytest
import respx
from httpx import Response

from ukcompanies import AsyncClient
from ukcompanies.exceptions import NotFoundError, ValidationError
from ukcompanies.models.filing import FilingCategory


@pytest.mark.asyncio
class TestFilingHistory:
    """Test filing history endpoint."""

    async def test_filing_history_success(self):
        """Test successful filing history retrieval."""
        mock_response = {
            "items": [
                {
                    "transaction_id": "MzM2NTY5MzQ1OGFkaXF6a2N4",
                    "category": "accounts",
                    "date": "2024-01-15",
                    "description": "Annual accounts made up to 31 December 2023",
                    "type": "AA",
                    "barcode": "X1234567",
                    "pages": 25,
                    "links": {
                        "self": "/company/12345678/filing-history/MzM2NTY5MzQ1OGFkaXF6a2N4",
                        "document_metadata": "/document/doc123"
                    }
                },
                {
                    "transaction_id": "MzM2NTY5MzQ1OGFkaXF6a2N5",
                    "category": "confirmation-statement",
                    "date": "2024-02-01",
                    "description": "Confirmation statement made on 1 February 2024",
                    "type": "CS01",
                    "links": {
                        "self": "/company/12345678/filing-history/MzM2NTY5MzQ1OGFkaXF6a2N5"
                    }
                }
            ],
            "total_count": 50,
            "items_per_page": 25,
            "start_index": 0,
            "filing_history_status": "filing-history-available"
        }

        async with AsyncClient(api_key="test_key") as client:
            with respx.mock:
                # Mock the API response
                route = respx.get(
                    "https://api.company-information.service.gov.uk/company/12345678/filing-history"
                ).mock(
                    return_value=Response(
                        200,
                        json=mock_response,
                        headers={
                            "X-Ratelimit-Remain": "599",
                            "X-Ratelimit-Limit": "600",
                            "X-Ratelimit-Reset": "1234567890"
                        }
                    )
                )

                # Make the request
                result = await client.filing_history("12345678")

                # Verify the request was made
                assert route.called
                assert route.call_count == 1

                # Check the result
                assert result.total_count == 50
                assert result.items_per_page == 25
                assert result.start_index == 0
                assert result.filing_history_status == "filing-history-available"
                assert len(result.items) == 2

                # Check first item
                first_item = result.items[0]
                assert first_item.transaction_id == "MzM2NTY5MzQ1OGFkaXF6a2N4"
                assert first_item.category == "accounts"
                assert first_item.filing_date == date(2024, 1, 15)
                assert first_item.description == "Annual accounts made up to 31 December 2023"
                assert first_item.type == "AA"
                assert first_item.barcode == "X1234567"
                assert first_item.pages == 25
                assert first_item.links.document_metadata == "/document/doc123"

                # Check second item
                second_item = result.items[1]
                assert second_item.transaction_id == "MzM2NTY5MzQ1OGFkaXF6a2N5"
                assert second_item.category == "confirmation-statement"
                assert second_item.filing_date == date(2024, 2, 1)
                assert second_item.type == "CS01"
                assert second_item.barcode is None
                assert second_item.pages is None

    async def test_filing_history_with_category_filter(self):
        """Test filing history with category filter."""
        mock_response = {
            "items": [
                {
                    "transaction_id": "MzM2NTY5MzQ1OGFkaXF6a2N4",
                    "category": "accounts",
                    "date": "2024-01-15",
                    "description": "Annual accounts made up to 31 December 2023",
                    "type": "AA"
                }
            ],
            "total_count": 10,
            "items_per_page": 25,
            "start_index": 0
        }

        async with AsyncClient(api_key="test_key") as client:
            with respx.mock:
                # Mock the API response with category parameter
                route = respx.get(
                    "https://api.company-information.service.gov.uk/company/12345678/filing-history",
                    params={"category": "accounts", "items_per_page": 25, "start_index": 0}
                ).mock(
                    return_value=Response(
                        200,
                        json=mock_response,
                        headers={
                            "X-Ratelimit-Remain": "599",
                            "X-Ratelimit-Limit": "600",
                            "X-Ratelimit-Reset": "1234567890"
                        }
                    )
                )

                # Make the request with category filter
                result = await client.filing_history("12345678", category=FilingCategory.ACCOUNTS)

                # Verify the request was made with correct parameters
                assert route.called
                assert route.call_count == 1

                # Check the result
                assert result.total_count == 10
                assert len(result.items) == 1
                assert result.items[0].category == "accounts"

    async def test_filing_history_pagination(self):
        """Test filing history pagination."""
        mock_response = {
            "items": [],
            "total_count": 100,
            "items_per_page": 50,
            "start_index": 50
        }

        async with AsyncClient(api_key="test_key") as client:
            with respx.mock:
                # Mock the API response with pagination parameters
                route = respx.get(
                    "https://api.company-information.service.gov.uk/company/12345678/filing-history",
                    params={"items_per_page": 50, "start_index": 50}
                ).mock(
                    return_value=Response(
                        200,
                        json=mock_response,
                        headers={
                            "X-Ratelimit-Remain": "599",
                            "X-Ratelimit-Limit": "600",
                            "X-Ratelimit-Reset": "1234567890"
                        }
                    )
                )

                # Make the request with pagination
                result = await client.filing_history("12345678", items_per_page=50, start_index=50)

                # Verify the request was made with correct parameters
                assert route.called
                assert route.call_count == 1

                # Check the result
                assert result.total_count == 100
                assert result.items_per_page == 50
                assert result.start_index == 50

    async def test_filing_history_invalid_company(self):
        """Test filing history with invalid company number."""
        async with AsyncClient(api_key="test_key") as client:
            with pytest.raises(ValidationError) as exc_info:
                await client.filing_history("INVALID")

            assert "Invalid company number format" in str(exc_info.value)

    async def test_filing_history_not_found(self):
        """Test filing history when company doesn't exist."""
        async with AsyncClient(api_key="test_key") as client:
            with respx.mock:
                # Mock 404 response
                route = respx.get(
                    "https://api.company-information.service.gov.uk/company/99999999/filing-history"
                ).mock(
                    return_value=Response(
                        404,
                        json={"error": "company-profile-not-found"}
                    )
                )

                # Make the request
                with pytest.raises(NotFoundError) as exc_info:
                    await client.filing_history("99999999")

                assert route.called
                assert "not found" in str(exc_info.value).lower()


@pytest.mark.asyncio
class TestFilingTransaction:
    """Test filing transaction endpoint."""

    async def test_filing_transaction_success(self):
        """Test successful filing transaction retrieval."""
        mock_response = {
            "transaction_id": "MzM2NTY5MzQ1OGFkaXF6a2N4",
            "category": "accounts",
            "date": "2024-01-15",
            "description": "Annual accounts made up to 31 December 2023",
            "type": "AA",
            "subcategory": "small",
            "barcode": "X1234567",
            "pages": 25,
            "links": {
                "self": "/company/12345678/filing-history/MzM2NTY5MzQ1OGFkaXF6a2N4",
                "document_metadata": "/document/doc123"
            },
            "paper_filed": False,
            "action_date": "2024-01-14",
            "description_values": {
                "made_up_date": "2023-12-31"
            },
            "annotations": [
                {
                    "category": "accounts",
                    "description": "ACCOUNTS-TYPE-SMALL"
                }
            ]
        }

        async with AsyncClient(api_key="test_key") as client:
            with respx.mock:
                # Mock the API response
                route = respx.get(
                    "https://api.company-information.service.gov.uk/company/12345678/filing-history/MzM2NTY5MzQ1OGFkaXF6a2N4"
                ).mock(
                    return_value=Response(
                        200,
                        json=mock_response,
                        headers={
                            "X-Ratelimit-Remain": "599",
                            "X-Ratelimit-Limit": "600",
                            "X-Ratelimit-Reset": "1234567890"
                        }
                    )
                )

                # Make the request
                result = await client.filing_transaction("12345678", "MzM2NTY5MzQ1OGFkaXF6a2N4")

                # Verify the request was made
                assert route.called
                assert route.call_count == 1

                # Check the result
                assert result.transaction_id == "MzM2NTY5MzQ1OGFkaXF6a2N4"
                assert result.category == "accounts"
                assert result.filing_date == date(2024, 1, 15)
                assert result.description == "Annual accounts made up to 31 December 2023"
                assert result.type == "AA"
                assert result.subcategory == "small"
                assert result.barcode == "X1234567"
                assert result.pages == 25
                assert result.paper_filed is False
                assert result.action_date == date(2024, 1, 14)
                assert result.description_values["made_up_date"] == "2023-12-31"
                assert len(result.annotations) == 1

    async def test_filing_transaction_empty_id(self):
        """Test filing transaction with empty transaction ID."""
        async with AsyncClient(api_key="test_key") as client:
            with pytest.raises(ValidationError) as exc_info:
                await client.filing_transaction("12345678", "")

            assert "Transaction ID cannot be empty" in str(exc_info.value)

    async def test_filing_transaction_not_found(self):
        """Test filing transaction when transaction doesn't exist."""
        async with AsyncClient(api_key="test_key") as client:
            with respx.mock:
                # Mock 404 response
                route = respx.get(
                    "https://api.company-information.service.gov.uk/company/12345678/filing-history/INVALID"
                ).mock(
                    return_value=Response(
                        404,
                        json={"error": "filing-history-item-not-found"}
                    )
                )

                # Make the request
                with pytest.raises(NotFoundError) as exc_info:
                    await client.filing_transaction("12345678", "INVALID")

                assert route.called
                assert "not found" in str(exc_info.value).lower()


@pytest.mark.asyncio
class TestFilingHistoryPagination:
    """Test filing history pagination generator."""

    async def test_filing_history_pages_generator(self):
        """Test filing history pages generator."""
        # Mock responses for multiple pages
        page1_response = {
            "items": [
                {
                    "transaction_id": f"transaction_{i}",
                    "category": "accounts",
                    "date": "2024-01-15",
                    "description": f"Filing {i}"
                }
                for i in range(10)
            ],
            "total_count": 25,
            "items_per_page": 10,
            "start_index": 0
        }

        page2_response = {
            "items": [
                {
                    "transaction_id": f"transaction_{i}",
                    "category": "accounts",
                    "date": "2024-01-15",
                    "description": f"Filing {i}"
                }
                for i in range(10, 20)
            ],
            "total_count": 25,
            "items_per_page": 10,
            "start_index": 10
        }

        page3_response = {
            "items": [
                {
                    "transaction_id": f"transaction_{i}",
                    "category": "accounts",
                    "date": "2024-01-15",
                    "description": f"Filing {i}"
                }
                for i in range(20, 25)
            ],
            "total_count": 25,
            "items_per_page": 10,
            "start_index": 20
        }

        async with AsyncClient(api_key="test_key") as client:
            with respx.mock:
                # Mock multiple page responses
                route1 = respx.get(
                    "https://api.company-information.service.gov.uk/company/12345678/filing-history",
                    params={"items_per_page": 10, "start_index": 0}
                ).mock(
                    return_value=Response(
                        200,
                        json=page1_response,
                        headers={
                            "X-Ratelimit-Remain": "599",
                            "X-Ratelimit-Limit": "600",
                            "X-Ratelimit-Reset": "1234567890"
                        }
                    )
                )

                route2 = respx.get(
                    "https://api.company-information.service.gov.uk/company/12345678/filing-history",
                    params={"items_per_page": 10, "start_index": 10}
                ).mock(
                    return_value=Response(
                        200,
                        json=page2_response,
                        headers={
                            "X-Ratelimit-Remain": "598",
                            "X-Ratelimit-Limit": "600",
                            "X-Ratelimit-Reset": "1234567890"
                        }
                    )
                )

                route3 = respx.get(
                    "https://api.company-information.service.gov.uk/company/12345678/filing-history",
                    params={"items_per_page": 10, "start_index": 20}
                ).mock(
                    return_value=Response(
                        200,
                        json=page3_response,
                        headers={
                            "X-Ratelimit-Remain": "597",
                            "X-Ratelimit-Limit": "600",
                            "X-Ratelimit-Reset": "1234567890"
                        }
                    )
                )

                # Collect all pages
                pages = []
                async for page in client.filing_history_pages("12345678", per_page=10):
                    pages.append(page)

                # Verify all pages were fetched
                assert len(pages) == 3
                assert route1.called
                assert route2.called
                assert route3.called

                # Check page details
                assert len(pages[0].items) == 10
                assert len(pages[1].items) == 10
                assert len(pages[2].items) == 5

                # Verify transaction IDs are sequential
                all_ids = []
                for page in pages:
                    all_ids.extend([item.transaction_id for item in page.items])

                expected_ids = [f"transaction_{i}" for i in range(25)]
                assert all_ids == expected_ids

    async def test_filing_history_pages_with_max_pages(self):
        """Test filing history pages generator with max pages limit."""
        # Mock response
        page_response = {
            "items": [
                {
                    "transaction_id": f"transaction_{i}",
                    "category": "accounts",
                    "date": "2024-01-15",
                    "description": f"Filing {i}"
                }
                for i in range(10)
            ],
            "total_count": 100,
            "items_per_page": 10,
            "start_index": 0
        }

        async with AsyncClient(api_key="test_key") as client:
            with respx.mock:
                # Mock first page response
                route = respx.get(
                    "https://api.company-information.service.gov.uk/company/12345678/filing-history",
                    params={"items_per_page": 10, "start_index": 0}
                ).mock(
                    return_value=Response(
                        200,
                        json=page_response,
                        headers={
                            "X-Ratelimit-Remain": "599",
                            "X-Ratelimit-Limit": "600",
                            "X-Ratelimit-Reset": "1234567890"
                        }
                    )
                )

                # Collect pages with max_pages=1
                pages = []
                async for page in client.filing_history_pages("12345678", per_page=10, max_pages=1):
                    pages.append(page)

                # Should only fetch one page
                assert len(pages) == 1
                assert route.called
                assert route.call_count == 1
