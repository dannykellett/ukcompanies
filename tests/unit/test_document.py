"""Unit tests for document models."""

from datetime import datetime

import pytest
from pydantic import ValidationError

from ukcompanies.models.document import (
    Document,
    DocumentContent,
    DocumentFormat,
    DocumentLinks,
    DocumentMetadata,
    DocumentResource,
)


class TestDocumentFormat:
    """Test DocumentFormat enum."""

    def test_document_format_values(self):
        """Test that document formats have correct MIME types."""
        assert DocumentFormat.PDF.value == "application/pdf"
        assert DocumentFormat.XHTML.value == "application/xhtml+xml"
        assert DocumentFormat.JSON.value == "application/json"
        assert DocumentFormat.CSV.value == "text/csv"
        assert DocumentFormat.XML.value == "application/xml"

    def test_document_format_from_string(self):
        """Test creating format from MIME type string."""
        format_pdf = DocumentFormat("application/pdf")
        assert format_pdf == DocumentFormat.PDF

        format_json = DocumentFormat("application/json")
        assert format_json == DocumentFormat.JSON


class TestDocumentLinks:
    """Test DocumentLinks model."""

    def test_document_links_minimal(self):
        """Test creating document links with minimal data."""
        links = DocumentLinks(self="/document/doc123")
        assert links.self == "/document/doc123"
        assert links.document is None

    def test_document_links_with_document(self):
        """Test creating document links with document URL."""
        links = DocumentLinks(
            self="/document/doc123",
            document="/document/doc123/content"
        )
        assert links.self == "/document/doc123"
        assert links.document == "/document/doc123/content"

    def test_document_links_missing_self(self):
        """Test that self link is required."""
        with pytest.raises(ValidationError) as exc_info:
            DocumentLinks()

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == ("self",)
        assert errors[0]["type"] == "missing"


class TestDocumentMetadata:
    """Test DocumentMetadata model."""

    def test_document_metadata_minimal(self):
        """Test creating metadata with minimal fields."""
        metadata = DocumentMetadata()
        assert metadata.company_number is None
        assert metadata.barcode is None
        assert metadata.category is None
        assert metadata.pages is None

    def test_document_metadata_complete(self):
        """Test creating metadata with all fields."""
        now = datetime.now()
        metadata = DocumentMetadata(
            company_number="12345678",
            barcode="X1234567",
            significant_date=now,
            significant_date_type="made-up-date",
            category="accounts",
            created_at=now,
            updated_at=now,
            etag="abc123",
            links=DocumentLinks(self="/document/doc123"),
            pages=25,
            filename="accounts.pdf",
            resources={
                "application/pdf": {
                    "content_type": "application/pdf",
                    "content_length": 1234567
                }
            }
        )
        assert metadata.company_number == "12345678"
        assert metadata.barcode == "X1234567"
        assert metadata.significant_date == now
        assert metadata.significant_date_type == "made-up-date"
        assert metadata.category == "accounts"
        assert metadata.created_at == now
        assert metadata.updated_at == now
        assert metadata.etag == "abc123"
        assert metadata.links.self == "/document/doc123"
        assert metadata.pages == 25
        assert metadata.filename == "accounts.pdf"
        assert "application/pdf" in metadata.resources


class TestDocumentResource:
    """Test DocumentResource model."""

    def test_document_resource_minimal(self):
        """Test creating resource with minimal fields."""
        resource = DocumentResource(content_type=DocumentFormat.PDF)
        assert resource.content_type == "application/pdf"
        assert resource.content_length is None
        assert resource.created_at is None
        assert resource.updated_at is None

    def test_document_resource_complete(self):
        """Test creating resource with all fields."""
        now = datetime.now()
        resource = DocumentResource(
            content_type=DocumentFormat.PDF,
            content_length=1234567,
            created_at=now,
            updated_at=now
        )
        assert resource.content_type == "application/pdf"
        assert resource.content_length == 1234567
        assert resource.created_at == now
        assert resource.updated_at == now

    def test_document_resource_missing_content_type(self):
        """Test that content_type is required."""
        with pytest.raises(ValidationError) as exc_info:
            DocumentResource()

        errors = exc_info.value.errors()
        assert any("content_type" in str(error) for error in errors)


class TestDocument:
    """Test Document model."""

    def test_document_minimal(self):
        """Test creating document with minimal fields."""
        document = Document(document_id="doc123")
        assert document.document_id == "doc123"
        assert document.company_number is None
        assert document.barcode is None
        assert document.available_formats == []
        assert document.resources == {}

    def test_document_complete(self):
        """Test creating document with all fields."""
        now = datetime.now()
        document = Document(
            document_id="doc123",
            company_number="12345678",
            barcode="X1234567",
            significant_date=now,
            significant_date_type="made-up-date",
            category="accounts",
            created_at=now,
            updated_at=now,
            available_formats=[DocumentFormat.PDF, DocumentFormat.XHTML],
            etag="abc123",
            links=DocumentLinks(self="/document/doc123"),
            pages=25,
            filename="accounts.pdf",
            resources={
                "application/pdf": DocumentResource(
                    content_type=DocumentFormat.PDF,
                    content_length=1234567
                )
            }
        )
        assert document.document_id == "doc123"
        assert document.company_number == "12345678"
        assert document.barcode == "X1234567"
        assert document.significant_date == now
        assert document.category == "accounts"
        assert len(document.available_formats) == 2
        assert DocumentFormat.PDF in document.available_formats
        assert DocumentFormat.XHTML in document.available_formats
        assert document.etag == "abc123"
        assert document.pages == 25
        assert "application/pdf" in document.resources

    def test_document_from_metadata(self):
        """Test creating Document from DocumentMetadata."""
        now = datetime.now()
        metadata = DocumentMetadata(
            company_number="12345678",
            barcode="X1234567",
            significant_date=now,
            significant_date_type="made-up-date",
            category="accounts",
            created_at=now,
            updated_at=now,
            etag="abc123",
            links=DocumentLinks(self="/document/doc123"),
            pages=25,
            filename="accounts.pdf",
            resources={
                "application/pdf": {
                    "content_type": "application/pdf",
                    "content_length": 1234567,
                    "created_at": now.isoformat(),
                    "updated_at": now.isoformat()
                },
                "application/xhtml+xml": {
                    "content_type": "application/xhtml+xml",
                    "content_length": 45678
                }
            }
        )

        document = Document.from_metadata("doc123", metadata)

        assert document.document_id == "doc123"
        assert document.company_number == "12345678"
        assert document.barcode == "X1234567"
        assert document.category == "accounts"
        assert len(document.available_formats) == 2
        assert DocumentFormat.PDF in document.available_formats
        assert DocumentFormat.XHTML in document.available_formats
        assert document.pages == 25
        assert "application/pdf" in document.resources
        assert "application/xhtml+xml" in document.resources
        assert document.resources["application/pdf"].content_length == 1234567

    def test_document_from_metadata_unknown_format(self):
        """Test that unknown formats are skipped when creating from metadata."""
        metadata = DocumentMetadata(
            resources={
                "application/pdf": {
                    "content_type": "application/pdf",
                    "content_length": 1234567
                },
                "application/unknown": {
                    "content_type": "application/unknown",
                    "content_length": 999
                }
            }
        )

        document = Document.from_metadata("doc123", metadata)

        assert len(document.available_formats) == 1
        assert DocumentFormat.PDF in document.available_formats
        assert "application/pdf" in document.resources
        assert "application/unknown" not in document.resources


class TestDocumentContent:
    """Test DocumentContent model."""

    def test_document_content_binary(self):
        """Test creating document content with binary data."""
        content = DocumentContent(
            document_id="doc123",
            content_type=DocumentFormat.PDF,
            content_length=1234567,
            content=b"PDF binary content",
            etag="abc123"
        )
        assert content.document_id == "doc123"
        assert content.content_type == "application/pdf"
        assert content.content_length == 1234567
        assert content.content == b"PDF binary content"
        assert content.text_content is None
        assert content.etag == "abc123"

    def test_document_content_text(self):
        """Test creating document content with text data."""
        content = DocumentContent(
            document_id="doc123",
            content_type=DocumentFormat.XHTML,
            content_length=45678,
            text_content="<html>Document content</html>",
            etag="def456"
        )
        assert content.document_id == "doc123"
        assert content.content_type == "application/xhtml+xml"
        assert content.content_length == 45678
        assert content.content is None
        assert content.text_content == "<html>Document content</html>"
        assert content.etag == "def456"

    def test_document_content_minimal(self):
        """Test creating document content with minimal fields."""
        content = DocumentContent(
            document_id="doc123",
            content_type=DocumentFormat.JSON
        )
        assert content.document_id == "doc123"
        assert content.content_type == "application/json"
        assert content.content_length is None
        assert content.content is None
        assert content.text_content is None
        assert content.etag is None

    def test_document_content_missing_required(self):
        """Test that required fields are validated."""
        with pytest.raises(ValidationError) as exc_info:
            DocumentContent(document_id="doc123")

        errors = exc_info.value.errors()
        assert any("content_type" in str(error) for error in errors)
