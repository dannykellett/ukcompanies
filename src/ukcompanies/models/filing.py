"""Filing history models for Companies House API responses."""

from datetime import date
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class FilingCategory(str, Enum):
    """Filing category types."""

    ACCOUNTS = "accounts"
    ANNUAL_RETURN = "annual-return"
    CAPITAL = "capital"
    CHANGE_OF_NAME = "change-of-name"
    INCORPORATION = "incorporation"
    LIQUIDATION = "liquidation"
    MORTGAGE = "mortgage"
    OFFICERS = "officers"
    RESOLUTION = "resolution"
    CONFIRMATION_STATEMENT = "confirmation-statement"
    ADDRESS = "address"
    OTHER = "other"


class FilingType(str, Enum):
    """Common filing type codes."""

    AA = "AA"  # Accounts
    AR01 = "AR01"  # Annual return
    IN01 = "IN01"  # Incorporation
    CH01 = "CH01"  # Change of name
    CS01 = "CS01"  # Confirmation statement
    AD01 = "AD01"  # Change of registered office address
    AP01 = "AP01"  # Appointment of director
    TM01 = "TM01"  # Termination of director
    MR01 = "MR01"  # Registration of charge/mortgage
    MR04 = "MR04"  # Satisfaction of charge/mortgage
    SH01 = "SH01"  # Return of allotment of shares
    RES01 = "RES01"  # Resolution
    RES15 = "RES15"  # Written resolution
    DS01 = "DS01"  # Striking off application
    OTHER = "OTHER"


class FilingLinks(BaseModel):
    """Links associated with a filing."""

    self: str = Field(..., description="Link to this filing resource")
    document_metadata: str | None = Field(
        None,
        description="Link to document metadata"
    )


class FilingTransaction(BaseModel):
    """Individual filing transaction details."""

    transaction_id: str = Field(..., description="Unique filing identifier")
    category: FilingCategory = Field(..., description="Filing category")
    filing_date: date = Field(..., alias="date", description="Filing date")
    description: str = Field(..., description="Filing description")
    type: str | None = Field(None, description="Specific document type")
    subcategory: str | None = Field(None, description="Filing subcategory")
    barcode: str | None = Field(None, description="Document barcode")
    pages: int | None = Field(None, description="Number of pages")
    links: FilingLinks | None = Field(None, description="Related links")
    paper_filed: bool | None = Field(None, description="Filed on paper")
    action_date: date | None = Field(None, description="Date action taken")
    description_values: dict[str, Any] | None = Field(
        None,
        description="Values used in description"
    )
    annotations: list[dict[str, Any]] | None = Field(
        None,
        description="Filing annotations"
    )

    class Config:
        """Pydantic config."""

        populate_by_name = True
        use_enum_values = True


class FilingHistoryList(BaseModel):
    """Paginated filing history response."""

    items: list[FilingTransaction] = Field(
        default_factory=list,
        description="List of filing transactions"
    )
    total_count: int = Field(0, description="Total number of filings")
    items_per_page: int = Field(25, description="Number of items per page")
    start_index: int = Field(0, description="Starting index for pagination")
    filing_history_status: str | None = Field(
        None,
        description="Status of filing history"
    )

    class Config:
        """Pydantic config."""

        populate_by_name = True


class FilingHistoryItem(BaseModel):
    """Simplified filing history item for listing."""

    transaction_id: str = Field(..., description="Unique filing identifier")
    category: FilingCategory = Field(..., description="Filing category")
    filing_date: date = Field(..., alias="date", description="Filing date")
    description: str = Field(..., description="Filing description")
    type: str | None = Field(None, description="Document type code")
    barcode: str | None = Field(None, description="Document barcode")
    links: FilingLinks | None = Field(None, description="Related links")

    class Config:
        """Pydantic config."""

        populate_by_name = True
        use_enum_values = True

