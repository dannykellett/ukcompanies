"""Officer models for UK Companies API."""

from datetime import date
from enum import Enum

from pydantic import Field, field_validator

from .address import Address
from .base import BaseModel


class OfficerRole(str, Enum):
    """Officer role types."""

    DIRECTOR = "director"
    SECRETARY = "secretary"
    LLP_MEMBER = "llp-member"
    LLP_DESIGNATED_MEMBER = "llp-designated-member"
    NOMINEE_DIRECTOR = "nominee-director"
    NOMINEE_SECRETARY = "nominee-secretary"
    CORPORATE_DIRECTOR = "corporate-director"
    CORPORATE_SECRETARY = "corporate-secretary"
    CORPORATE_LLP_MEMBER = "corporate-llp-member"
    CORPORATE_LLP_DESIGNATED_MEMBER = "corporate-llp-designated-member"
    CORPORATE_NOMINEE_DIRECTOR = "corporate-nominee-director"
    CORPORATE_NOMINEE_SECRETARY = "corporate-nominee-secretary"
    JUDICIAL_FACTOR = "judicial-factor"


class IdentificationType(str, Enum):
    """Officer identification types."""

    UK_LIMITED_COMPANY = "uk-limited-company"
    EEA_COMPANY = "eea-company"
    NON_EEA_COMPANY = "non-eea-company"
    OTHER = "other"


class PartialDate(BaseModel):
    """Privacy-compliant date with only month and year.

    This is used for officer date of birth to comply with privacy requirements.
    The API returns only month and year for privacy reasons.
    """

    month: int = Field(..., ge=1, le=12, description="Month (1-12)")
    year: int = Field(..., ge=1800, le=2100, description="Year")

    @field_validator("month")
    @classmethod
    def validate_month(cls, v: int) -> int:
        """Validate month is in valid range."""
        if not 1 <= v <= 12:
            raise ValueError(f"Month must be between 1 and 12, got {v}")
        return v

    @field_validator("year")
    @classmethod
    def validate_year(cls, v: int) -> int:
        """Validate year is reasonable."""
        if not 1800 <= v <= 2100:
            raise ValueError(f"Year must be between 1800 and 2100, got {v}")
        return v

    def __str__(self) -> str:
        """Format as MM/YYYY."""
        return f"{self.month:02d}/{self.year}"

    @property
    def as_tuple(self) -> tuple[int, int]:
        """Return as (year, month) tuple for comparisons."""
        return (self.year, self.month)


class Officer(BaseModel):
    """Represents a company officer."""

    # Identification
    name: str = Field(..., description="Officer's full name")
    officer_id: str | None = Field(None, description="Unique officer identifier")

    # Role and appointment
    officer_role: OfficerRole = Field(..., description="Officer's role in the company")
    appointed_on: date | None = Field(None, description="Date officer was appointed")
    resigned_on: date | None = Field(None, description="Date officer resigned")

    # Personal details (privacy-compliant)
    date_of_birth: PartialDate | None = Field(
        None,
        description="Month and year of birth only (privacy-compliant)"
    )
    nationality: str | None = Field(None, description="Officer's nationality")
    country_of_residence: str | None = Field(None, description="Country of residence")
    occupation: str | None = Field(None, description="Officer's occupation")

    # Corporate officer details
    identification: dict | None = Field(
        None,
        description="Corporate identification details"
    )

    # Address
    address: Address | None = Field(None, description="Service address")

    # Links
    links: dict | None = Field(None, description="API links for related resources")

    @property
    def is_active(self) -> bool:
        """Check if officer is currently active (not resigned)."""
        return self.resigned_on is None

    @property
    def is_corporate(self) -> bool:
        """Check if this is a corporate officer."""
        return self.officer_role in [
            OfficerRole.CORPORATE_DIRECTOR,
            OfficerRole.CORPORATE_SECRETARY,
            OfficerRole.CORPORATE_LLP_MEMBER,
            OfficerRole.CORPORATE_LLP_DESIGNATED_MEMBER,
            OfficerRole.CORPORATE_NOMINEE_DIRECTOR,
            OfficerRole.CORPORATE_NOMINEE_SECRETARY,
        ]

    @field_validator("officer_id")
    @classmethod
    def validate_officer_id(cls, v: str | None) -> str | None:
        """Validate officer ID format if provided."""
        if v is not None and not v.strip():
            return None
        return v


class OfficerList(BaseModel):
    """List of officers with pagination."""

    items: list[Officer] = Field(default_factory=list, description="List of officers")
    active_count: int | None = Field(None, description="Number of active officers")
    inactive_count: int | None = Field(None, description="Number of inactive officers")
    items_per_page: int | None = Field(None, description="Number of items per page")
    start_index: int | None = Field(None, description="Starting index for pagination")
    total_results: int | None = Field(None, description="Total number of results")
    resigned_count: int | None = Field(None, description="Number of resigned officers")

    # Links for pagination
    links: dict | None = Field(None, description="Links for pagination")

    @property
    def has_more_pages(self) -> bool:
        """Check if there are more pages available."""
        if self.total_results is None or self.start_index is None:
            return False
        if self.items_per_page is None:
            return False

        current_end = self.start_index + len(self.items)
        return current_end < self.total_results

    @property
    def next_start_index(self) -> int:
        """Calculate the start index for the next page."""
        if self.start_index is None:
            return 0
        if self.items_per_page is None:
            return self.start_index + len(self.items)
        return self.start_index + self.items_per_page
