"""Appointment models for UK Companies API."""

from datetime import date
from enum import Enum

from pydantic import Field

from .address import Address
from .base import BaseModel
from .officer import OfficerRole


class CompanyStatus(str, Enum):
    """Company status types."""

    ACTIVE = "active"
    DISSOLVED = "dissolved"
    LIQUIDATION = "liquidation"
    RECEIVERSHIP = "receivership"
    ADMINISTRATION = "administration"
    VOLUNTARY_ARRANGEMENT = "voluntary-arrangement"
    CONVERTED_CLOSED = "converted-closed"
    INSOLVENCY_PROCEEDINGS = "insolvency-proceedings"
    CLOSED = "closed"
    OPEN = "open"
    REGISTERED = "registered"
    REMOVED = "removed"


class Appointment(BaseModel):
    """Represents an officer's appointment to a company."""

    # Company information
    appointed_to: dict = Field(..., description="Company details for this appointment")

    # The appointed_to dict typically contains:
    # - company_name: str
    # - company_number: str
    # - company_status: str

    # Appointment details
    name: str = Field(..., description="Officer name for this appointment")
    officer_role: OfficerRole = Field(..., description="Role in this company")
    appointed_on: date | None = Field(None, description="Date appointed to this role")
    appointed_before: date | None = Field(
        None,
        description="Date appointed before this date (when exact date unknown)"
    )
    resigned_on: date | None = Field(None, description="Date resigned from this role")

    # Personal/corporate details
    nationality: str | None = Field(None, description="Nationality at time of appointment")
    country_of_residence: str | None = Field(None, description="Country of residence")
    occupation: str | None = Field(None, description="Occupation at time of appointment")

    # Address
    address: Address | None = Field(None, description="Service address for this appointment")

    # Identification
    identification: dict | None = Field(
        None,
        description="Corporate identification if corporate officer"
    )

    # Additional info
    is_pre_1992_appointment: bool | None = Field(
        None,
        description="Whether this appointment predates 1992"
    )
    person_number: str | None = Field(None, description="Internal person number")

    # Links
    links: dict | None = Field(None, description="API links for related resources")

    @property
    def company_name(self) -> str | None:
        """Get the company name from appointed_to."""
        if self.appointed_to:
            return self.appointed_to.get("company_name")
        return None

    @property
    def company_number(self) -> str | None:
        """Get the company number from appointed_to."""
        if self.appointed_to:
            return self.appointed_to.get("company_number")
        return None

    @property
    def company_status(self) -> str | None:
        """Get the company status from appointed_to."""
        if self.appointed_to:
            return self.appointed_to.get("company_status")
        return None

    @property
    def is_active(self) -> bool:
        """Check if appointment is currently active."""
        return self.resigned_on is None

    @property
    def is_corporate(self) -> bool:
        """Check if this is a corporate appointment."""
        return self.officer_role in [
            OfficerRole.CORPORATE_DIRECTOR,
            OfficerRole.CORPORATE_SECRETARY,
            OfficerRole.CORPORATE_LLP_MEMBER,
            OfficerRole.CORPORATE_LLP_DESIGNATED_MEMBER,
            OfficerRole.CORPORATE_NOMINEE_DIRECTOR,
            OfficerRole.CORPORATE_NOMINEE_SECRETARY,
        ]


class AppointmentList(BaseModel):
    """List of appointments with pagination."""

    items: list[Appointment] = Field(
        default_factory=list,
        description="List of appointments"
    )

    # Pagination metadata
    items_per_page: int | None = Field(None, description="Number of items per page")
    start_index: int | None = Field(None, description="Starting index for pagination")
    total_results: int | None = Field(None, description="Total number of results")

    # Additional metadata
    date_of_birth: dict | None = Field(
        None,
        description="Officer's date of birth (month/year only)"
    )
    is_corporate_officer: bool | None = Field(
        None,
        description="Whether this is a corporate officer"
    )
    kind: str | None = Field(None, description="Type of resource")
    name: str | None = Field(None, description="Officer's name")

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

    @property
    def active_appointments(self) -> list[Appointment]:
        """Get list of active appointments."""
        return [a for a in self.items if a.is_active]

    @property
    def resigned_appointments(self) -> list[Appointment]:
        """Get list of resigned appointments."""
        return [a for a in self.items if not a.is_active]
