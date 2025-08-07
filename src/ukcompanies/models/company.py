"""Company models for UK Companies API."""

from datetime import date
from enum import Enum
from typing import Any

from pydantic import Field, field_validator

from .address import Address
from .base import BaseModel


class CompanyStatus(str, Enum):
    """Company status enumeration."""

    ACTIVE = "active"
    DISSOLVED = "dissolved"
    LIQUIDATION = "liquidation"
    RECEIVERSHIP = "receivership"
    ADMINISTRATION = "administration"
    VOLUNTARY_ARRANGEMENT = "voluntary-arrangement"
    CONVERTED_CLOSED = "converted-closed"
    INSOLVENCY_PROCEEDINGS = "insolvency-proceedings"


class CompanyType(str, Enum):
    """Company type enumeration."""

    LTD = "ltd"  # Private limited company
    PLC = "plc"  # Public limited company
    OLD_PUBLIC_COMPANY = "old-public-company"
    PRIVATE_UNLIMITED = "private-unlimited"
    LIMITED_PARTNERSHIP = "limited-partnership"
    LIMITED_LIABILITY_PARTNERSHIP = "llp"
    INDUSTRIAL_PROVIDENT_SOCIETY = "industrial-and-provident-society"
    CHARITABLE_INCORPORATED_ORGANISATION = "charitable-incorporated-organisation"
    SCOTTISH_PARTNERSHIP = "scottish-partnership"
    ROYAL_CHARTER = "royal-charter"
    INVESTMENT_COMPANY = "investment-company-with-variable-capital"
    UNREGISTERED_COMPANY = "unregistered-company"
    OTHER = "other"


class Jurisdiction(str, Enum):
    """Jurisdiction enumeration."""

    ENGLAND_WALES = "england-wales"
    SCOTLAND = "scotland"
    NORTHERN_IRELAND = "northern-ireland"
    WALES = "wales"
    ENGLAND = "england"
    UK = "united-kingdom"
    NONEU = "noneu"
    EU = "european-union"


class AccountingReference(BaseModel):
    """Accounting reference date information."""

    day: int | None = Field(None, description="Day of month", ge=1, le=31)
    month: int | None = Field(None, description="Month", ge=1, le=12)

    @field_validator("day")
    @classmethod
    def validate_day(cls, v: int | None, values: dict[str, Any]) -> int | None:
        """Validate day is valid for the month."""
        if v is None:
            return v
        # Basic validation - could be enhanced with month-specific logic
        if not 1 <= v <= 31:
            raise ValueError("Day must be between 1 and 31")
        return v


class ConfirmationStatement(BaseModel):
    """Confirmation statement information."""

    next_due: date | None = Field(None, description="Next statement due date")
    overdue: bool = Field(False, description="Whether statement is overdue")
    next_made_up_to: date | None = Field(None, description="Next statement period end")
    last_made_up_to: date | None = Field(None, description="Last statement period end")


class Accounts(BaseModel):
    """Company accounts information."""

    accounting_reference_date: AccountingReference | None = Field(
        None, description="Accounting reference date"
    )
    next_due: date | None = Field(None, description="Next accounts due date")
    last_accounts: dict[str, Any] | None = Field(None, description="Last accounts details")
    next_accounts: dict[str, Any] | None = Field(None, description="Next accounts details")
    overdue: bool = Field(False, description="Whether accounts are overdue")


class Company(BaseModel):
    """Represents a UK company."""

    company_number: str = Field(..., description="Unique 8-character identifier")
    company_name: str = Field(..., description="Registered company name")
    company_status: str | None = Field(None, description="Company status")
    company_status_detail: str | None = Field(None, description="Additional status details")
    date_of_creation: date | None = Field(None, description="Company incorporation date")
    date_of_cessation: date | None = Field(None, description="Company cessation date")
    type: str | None = Field(None, description="Company type")
    jurisdiction: str | None = Field(None, description="Registration jurisdiction")
    sic_codes: list[str] | None = Field(
        None, description="Standard Industrial Classification codes"
    )
    registered_office_address: Address | None = Field(None, description="Official company address")
    accounts: Accounts | None = Field(None, description="Accounting information")
    confirmation_statement: ConfirmationStatement | None = Field(
        None, description="Annual confirmation info"
    )
    has_been_liquidated: bool = Field(False, description="Whether company has been liquidated")
    has_insolvency_history: bool = Field(
        False, description="Whether company has insolvency history"
    )
    etag: str | None = Field(None, description="ETag for caching")
    can_file: bool = Field(True, description="Whether company can file documents")
    undeliverable_registered_office_address: bool = Field(
        False, description="Whether mail to registered office is undeliverable"
    )
    registered_office_is_in_dispute: bool = Field(
        False, description="Whether registered office is disputed"
    )
    links: dict[str, str] | None = Field(None, description="Related resource links")

    @field_validator("company_number")
    @classmethod
    def validate_company_number(cls, v: str) -> str:
        """Validate company number format."""
        # Remove spaces and convert to uppercase
        normalized = v.strip().upper().replace(" ", "")

        # Check length
        if len(normalized) != 8:
            # Try padding numeric values
            if normalized.isdigit() and 7 <= len(normalized) <= 8:
                normalized = normalized.zfill(8)
            else:
                raise ValueError(f"Company number must be 8 characters: {v}")

        return normalized

    @property
    def is_active(self) -> bool:
        """Check if company is active."""
        return self.company_status == CompanyStatus.ACTIVE.value

    @property
    def is_dissolved(self) -> bool:
        """Check if company is dissolved."""
        return self.company_status == CompanyStatus.DISSOLVED.value

    @property
    def display_status(self) -> str:
        """Get human-readable status."""
        if self.company_status_detail:
            return self.company_status_detail
        if self.company_status:
            return self.company_status.replace("-", " ").title()
        return "Unknown"
