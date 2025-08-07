"""Document models for Companies House API responses."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class DocumentFormat(str, Enum):
    """Available document formats."""

    PDF = "application/pdf"
    XHTML = "application/xhtml+xml"
    JSON = "application/json"
    CSV = "text/csv"
    XML = "application/xml"


class DocumentLinks(BaseModel):
    """Links associated with a document."""

    self: str = Field(..., description="Link to this document resource")
    document: str | None = Field(None, description="Link to document content")


class DocumentMetadata(BaseModel):
    """Document metadata information."""

    company_number: str | None = Field(None, description="Associated company number")
    barcode: str | None = Field(None, description="Document barcode")
    significant_date: datetime | None = Field(None, description="Document significant date")
    significant_date_type: str | None = Field(None, description="Type of significant date")
    category: str | None = Field(None, description="Document category")
    created_at: datetime | None = Field(None, description="Document creation timestamp")
    updated_at: datetime | None = Field(None, description="Last update timestamp")
    etag: str | None = Field(None, description="Document version identifier")
    links: DocumentLinks | None = Field(None, description="Related links")
    pages: int | None = Field(None, description="Number of pages")
    filename: str | None = Field(None, description="Original filename")
    resources: dict[str, dict] | None = Field(None, description="Available resources")

    class Config:
        """Pydantic config."""

        populate_by_name = True


class DocumentResource(BaseModel):
    """Document resource with format information."""

    content_type: DocumentFormat = Field(..., description="MIME type of the resource")
    content_length: int | None = Field(None, description="Size in bytes")
    created_at: datetime | None = Field(None, description="Resource creation time")
    updated_at: datetime | None = Field(None, description="Resource update time")

    class Config:
        """Pydantic config."""

        populate_by_name = True
        use_enum_values = True


class Document(BaseModel):
    """Full document model with metadata and resources."""

    document_id: str = Field(..., description="Unique document identifier")
    company_number: str | None = Field(None, description="Associated company if applicable")
    barcode: str | None = Field(None, description="Document barcode")
    significant_date: datetime | None = Field(None, description="Document significant date")
    significant_date_type: str | None = Field(None, description="Type of significant date")
    category: str | None = Field(None, description="Document category")
    created_at: datetime | None = Field(None, description="Document creation timestamp")
    updated_at: datetime | None = Field(None, description="Last update timestamp")
    available_formats: list[DocumentFormat] = Field(
        default_factory=list,
        description="List of available formats"
    )
    etag: str | None = Field(None, description="Document version identifier")
    links: DocumentLinks | None = Field(None, description="Related links")
    pages: int | None = Field(None, description="Number of pages")
    filename: str | None = Field(None, description="Original filename")
    resources: dict[str, DocumentResource] = Field(
        default_factory=dict,
        description="Available document resources by format"
    )

    class Config:
        """Pydantic config."""

        populate_by_name = True

    @classmethod
    def from_metadata(cls, document_id: str, metadata: DocumentMetadata) -> "Document":
        """Create Document from DocumentMetadata.

        Args:
            document_id: The document ID
            metadata: The document metadata

        Returns:
            Document instance
        """
        # Extract available formats from resources
        available_formats = []
        resources = {}

        if metadata.resources:
            for key, resource_data in metadata.resources.items():
                if "content_type" in resource_data:
                    content_type = resource_data["content_type"]
                    try:
                        format_enum = DocumentFormat(content_type)
                        available_formats.append(format_enum)
                        resources[key] = DocumentResource(**resource_data)
                    except ValueError:
                        # Skip unknown formats
                        pass

        return cls(
            document_id=document_id,
            company_number=metadata.company_number,
            barcode=metadata.barcode,
            significant_date=metadata.significant_date,
            significant_date_type=metadata.significant_date_type,
            category=metadata.category,
            created_at=metadata.created_at,
            updated_at=metadata.updated_at,
            available_formats=available_formats,
            etag=metadata.etag,
            links=metadata.links,
            pages=metadata.pages,
            filename=metadata.filename,
            resources=resources
        )


class DocumentContent(BaseModel):
    """Document content response."""

    document_id: str = Field(..., description="Document identifier")
    content_type: DocumentFormat = Field(..., description="Content MIME type")
    content_length: int | None = Field(None, description="Content size in bytes")
    content: bytes | None = Field(None, description="Binary content for PDFs")
    text_content: str | None = Field(None, description="Text content for XHTML/JSON")
    etag: str | None = Field(None, description="Document version identifier")

    class Config:
        """Pydantic config."""

        populate_by_name = True
        use_enum_values = True

