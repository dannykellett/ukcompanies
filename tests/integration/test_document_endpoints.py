"""Integration tests for document endpoints."""


import pytest
import respx
from httpx import Response

from ukcompanies import AsyncClient
from ukcompanies.exceptions import NotFoundError, ValidationError
from ukcompanies.models.document import DocumentFormat


@pytest.mark.asyncio
class TestDocumentMetadata:
    """Test document metadata endpoint."""

    async def test_document_metadata_success(self):
        """Test successful document metadata retrieval."""
        mock_response = {
            "company_number": "12345678",
            "barcode": "X1234567",
            "significant_date": "2023-12-31T00:00:00Z",
            "significant_date_type": "made-up-date",
            "category": "accounts",
            "created_at": "2024-01-15T10:30:00Z",
            "updated_at": "2024-01-15T10:35:00Z",
            "etag": "abc123def456",
            "links": {
                "self": "/document/doc123",
                "document": "/document/doc123/content"
            },
            "pages": 25,
            "filename": "accounts.pdf",
            "resources": {
                "application/pdf": {
                    "content_type": "application/pdf",
                    "content_length": 1234567,
                    "created_at": "2024-01-15T10:30:00Z",
                    "updated_at": "2024-01-15T10:35:00Z"
                },
                "application/xhtml+xml": {
                    "content_type": "application/xhtml+xml",
                    "content_length": 45678,
                    "created_at": "2024-01-15T10:30:00Z"
                }
            }
        }

        async with AsyncClient(api_key="test_key") as client:
            with respx.mock:
                # Mock the API response
                route = respx.get(
                    "https://api.company-information.service.gov.uk/document/doc123"
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
                result = await client.document("doc123")

                # Verify the request was made
                assert route.called
                assert route.call_count == 1

                # Check the result
                assert result.document_id == "doc123"
                assert result.company_number == "12345678"
                assert result.barcode == "X1234567"
                assert result.category == "accounts"
                assert result.pages == 25
                assert result.filename == "accounts.pdf"
                assert result.etag == "abc123def456"

                # Check available formats
                assert len(result.available_formats) == 2
                assert DocumentFormat.PDF in result.available_formats
                assert DocumentFormat.XHTML in result.available_formats

                # Check resources
                assert "application/pdf" in result.resources
                assert result.resources["application/pdf"].content_length == 1234567
                assert "application/xhtml+xml" in result.resources
                assert result.resources["application/xhtml+xml"].content_length == 45678

                # Check links
                assert result.links.self == "/document/doc123"
                assert result.links.document == "/document/doc123/content"

    async def test_document_metadata_minimal(self):
        """Test document metadata with minimal fields."""
        mock_response = {
            "links": {
                "self": "/document/doc456"
            }
        }

        async with AsyncClient(api_key="test_key") as client:
            with respx.mock:
                # Mock the API response
                route = respx.get(
                    "https://api.company-information.service.gov.uk/document/doc456"
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
                result = await client.document("doc456")

                # Verify the request was made
                assert route.called

                # Check the result
                assert result.document_id == "doc456"
                assert result.company_number is None
                assert result.barcode is None
                assert result.available_formats == []
                assert result.resources == {}

    async def test_document_metadata_empty_id(self):
        """Test document metadata with empty document ID."""
        async with AsyncClient(api_key="test_key") as client:
            with pytest.raises(ValidationError) as exc_info:
                await client.document("")

            assert "Document ID cannot be empty" in str(exc_info.value)

    async def test_document_metadata_not_found(self):
        """Test document metadata when document doesn't exist."""
        async with AsyncClient(api_key="test_key") as client:
            with respx.mock:
                # Mock 404 response
                route = respx.get(
                    "https://api.company-information.service.gov.uk/document/INVALID"
                ).mock(
                    return_value=Response(
                        404,
                        json={"error": "document-not-found"}
                    )
                )

                # Make the request
                with pytest.raises(NotFoundError) as exc_info:
                    await client.document("INVALID")

                assert route.called
                assert "not found" in str(exc_info.value).lower()


@pytest.mark.asyncio
class TestDocumentContent:
    """Test document content endpoint."""

    async def test_document_content_pdf(self):
        """Test retrieving PDF document content."""
        pdf_content = b"%PDF-1.4\n%Binary content here..."

        async with AsyncClient(api_key="test_key") as client:
            with respx.mock:
                # Mock the API response for PDF content
                route = respx.get(
                    "https://api.company-information.service.gov.uk/document/doc123/content"
                ).mock(
                    return_value=Response(
                        200,
                        content=pdf_content,
                        headers={
                            "Content-Type": "application/pdf",
                            "ETag": "pdf-etag-123",
                            "X-Ratelimit-Remain": "599",
                            "X-Ratelimit-Limit": "600",
                            "X-Ratelimit-Reset": "1234567890"
                        }
                    )
                )

                # Make the request
                result = await client.document_content("doc123", format=DocumentFormat.PDF)

                # Verify the request was made with correct Accept header
                assert route.called
                assert route.call_count == 1

                # Check the result
                assert result.document_id == "doc123"
                assert result.content_type == DocumentFormat.PDF
                assert result.content == pdf_content
                assert result.content_length == len(pdf_content)
                assert result.etag == "pdf-etag-123"
                assert result.text_content is None

    async def test_document_content_xhtml(self):
        """Test retrieving XHTML document content."""
        xhtml_content = "<html><body><h1>Document Content</h1></body></html>"

        async with AsyncClient(api_key="test_key") as client:
            with respx.mock:
                # Mock the API response for XHTML content
                route = respx.get(
                    "https://api.company-information.service.gov.uk/document/doc123/content"
                ).mock(
                    return_value=Response(
                        200,
                        text=xhtml_content,
                        headers={
                            "Content-Type": "application/xhtml+xml",
                            "ETag": "xhtml-etag-456",
                            "X-Ratelimit-Remain": "599",
                            "X-Ratelimit-Limit": "600",
                            "X-Ratelimit-Reset": "1234567890"
                        }
                    )
                )

                # Make the request
                result = await client.document_content("doc123", format=DocumentFormat.XHTML)

                # Verify the request was made
                assert route.called
                assert route.call_count == 1

                # Check the result
                assert result.document_id == "doc123"
                assert result.content_type == DocumentFormat.XHTML
                assert result.text_content == xhtml_content
                assert result.content_length == len(xhtml_content)
                assert result.etag == "xhtml-etag-456"
                assert result.content is None

    async def test_document_content_json(self):
        """Test retrieving JSON document content."""
        json_content = '{"data": {"accounts": {"period_end": "2023-12-31"}}}'

        async with AsyncClient(api_key="test_key") as client:
            with respx.mock:
                # Mock the API response for JSON content
                route = respx.get(
                    "https://api.company-information.service.gov.uk/document/doc123/content"
                ).mock(
                    return_value=Response(
                        200,
                        text=json_content,
                        headers={
                            "Content-Type": "application/json",
                            "ETag": "json-etag-789",
                            "X-Ratelimit-Remain": "599",
                            "X-Ratelimit-Limit": "600",
                            "X-Ratelimit-Reset": "1234567890"
                        }
                    )
                )

                # Make the request
                result = await client.document_content("doc123", format="application/json")

                # Verify the request was made
                assert route.called
                assert route.call_count == 1

                # Check the result
                assert result.document_id == "doc123"
                assert result.content_type == DocumentFormat.JSON
                assert result.text_content == json_content
                assert result.content_length == len(json_content)
                assert result.etag == "json-etag-789"
                assert result.content is None

    async def test_document_content_csv(self):
        """Test retrieving CSV document content."""
        csv_content = "Name,Date,Amount\nCompany A,2023-12-31,1000000\n"

        async with AsyncClient(api_key="test_key") as client:
            with respx.mock:
                # Mock the API response for CSV content
                route = respx.get(
                    "https://api.company-information.service.gov.uk/document/doc123/content"
                ).mock(
                    return_value=Response(
                        200,
                        text=csv_content,
                        headers={
                            "Content-Type": "text/csv",
                            "X-Ratelimit-Remain": "599",
                            "X-Ratelimit-Limit": "600",
                            "X-Ratelimit-Reset": "1234567890"
                        }
                    )
                )

                # Make the request
                result = await client.document_content("doc123", format=DocumentFormat.CSV)

                # Verify the request was made
                assert route.called

                # Check the result
                assert result.document_id == "doc123"
                assert result.content_type == DocumentFormat.CSV
                assert result.text_content == csv_content
                assert result.content_length == len(csv_content)
                assert result.content is None

    async def test_document_content_no_format_specified(self):
        """Test retrieving document content without specifying format."""
        pdf_content = b"%PDF-1.4\n%Binary content..."

        async with AsyncClient(api_key="test_key") as client:
            with respx.mock:
                # Mock the API response - server decides format
                route = respx.get(
                    "https://api.company-information.service.gov.uk/document/doc123/content"
                ).mock(
                    return_value=Response(
                        200,
                        content=pdf_content,
                        headers={
                            "Content-Type": "application/pdf",
                            "X-Ratelimit-Remain": "599",
                            "X-Ratelimit-Limit": "600",
                            "X-Ratelimit-Reset": "1234567890"
                        }
                    )
                )

                # Make the request without specifying format
                result = await client.document_content("doc123")

                # Verify the request was made
                assert route.called

                # Check the result - should detect PDF from content-type
                assert result.document_id == "doc123"
                assert result.content_type == DocumentFormat.PDF
                assert result.content == pdf_content

    async def test_document_content_empty_id(self):
        """Test document content with empty document ID."""
        async with AsyncClient(api_key="test_key") as client:
            with pytest.raises(ValidationError) as exc_info:
                await client.document_content("")

            assert "Document ID cannot be empty" in str(exc_info.value)

    async def test_document_content_not_found(self):
        """Test document content when document doesn't exist."""
        async with AsyncClient(api_key="test_key") as client:
            with respx.mock:
                # Mock 404 response
                route = respx.get(
                    "https://api.company-information.service.gov.uk/document/INVALID/content"
                ).mock(
                    return_value=Response(
                        404,
                        json={"error": "document-not-found"}
                    )
                )

                # Make the request
                with pytest.raises(NotFoundError) as exc_info:
                    await client.document_content("INVALID")

                assert route.called
                assert "not found" in str(exc_info.value).lower()

    async def test_document_content_format_not_available(self):
        """Test document content when requested format is not available."""
        async with AsyncClient(api_key="test_key") as client:
            with respx.mock:
                # Mock 404 response for unavailable format
                route = respx.get(
                    "https://api.company-information.service.gov.uk/document/doc123/content"
                ).mock(
                    return_value=Response(
                        404,
                        json={"error": "format-not-available"}
                    )
                )

                # Make the request
                with pytest.raises(NotFoundError) as exc_info:
                    await client.document_content("doc123", format=DocumentFormat.CSV)

                assert route.called
                assert "not found" in str(exc_info.value).lower()

    async def test_document_content_large_pdf(self):
        """Test retrieving large PDF document content (streaming)."""
        # Simulate a 10MB PDF
        large_pdf_content = b"%PDF-1.4\n" + b"x" * (10 * 1024 * 1024)

        async with AsyncClient(api_key="test_key") as client:
            with respx.mock:
                # Mock the API response for large PDF
                route = respx.get(
                    "https://api.company-information.service.gov.uk/document/doc123/content"
                ).mock(
                    return_value=Response(
                        200,
                        content=large_pdf_content,
                        headers={
                            "Content-Type": "application/pdf",
                            "Content-Length": str(len(large_pdf_content)),
                            "X-Ratelimit-Remain": "599",
                            "X-Ratelimit-Limit": "600",
                            "X-Ratelimit-Reset": "1234567890"
                        }
                    )
                )

                # Make the request
                result = await client.document_content("doc123", format=DocumentFormat.PDF)

                # Verify the request was made
                assert route.called

                # Check the result
                assert result.document_id == "doc123"
                assert result.content_type == DocumentFormat.PDF
                assert result.content == large_pdf_content
                assert result.content_length == len(large_pdf_content)
                assert result.text_content is None
