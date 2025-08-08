"""Disqualification models for UK Companies API."""

from datetime import date
from enum import Enum

from pydantic import Field

from .address import Address
from .base import BaseModel


class DisqualificationReason(str, Enum):
    """Disqualification reason types."""

    MISCONDUCT = "misconduct"
    UNFITNESS = "unfitness"
    BREACH_OF_FIDUCIARY_DUTY = "breach-of-fiduciary-duty"
    WRONGFUL_TRADING = "wrongful-trading"
    FRAUDULENT_TRADING = "fraudulent-trading"
    FRAUD = "fraud"
    BREACH_OF_COMPANIES_ACT = "breach-of-companies-act"
    OTHER = "other"


class Disqualification(BaseModel):
    """Represents a disqualification order or undertaking."""

    # Disqualification period
    disqualified_from: date = Field(..., description="Start date of disqualification")
    disqualified_until: date = Field(..., description="End date of disqualification")

    # Reason and details
    reason: dict | None = Field(
        None,
        description="Reason for disqualification with description and act"
    )

    # The reason dict typically contains:
    # - description_identifier: str (e.g., "misconduct")
    # - act: str (e.g., "company-directors-disqualification-act-1986")
    # - section: str (e.g., "section-8")
    # - description: str (full text description)

    # Court order details
    court_name: str | None = Field(None, description="Court that issued the order")
    court_order_date: date | None = Field(None, description="Date of court order")
    case_identifier: str | None = Field(None, description="Court case reference")

    # Undertaking details (alternative to court order)
    undertaken_on: date | None = Field(
        None,
        description="Date disqualification undertaking was given"
    )

    # Company details (companies involved in the disqualification)
    company_names: list[str] | None = Field(
        default=None,
        description="Names of companies involved"
    )

    # Address
    address: Address | None = Field(None, description="Last known address")

    # Additional information
    heard_on: date | None = Field(None, description="Date case was heard")
    is_undertaking: bool | None = Field(
        None,
        description="Whether this is an undertaking rather than court order"
    )

    @property
    def is_active(self) -> bool:
        """Check if disqualification is currently active."""
        from datetime import date as dt
        today = dt.today()
        return self.disqualified_from <= today <= self.disqualified_until

    @property
    def has_expired(self) -> bool:
        """Check if disqualification has expired."""
        from datetime import date as dt
        today = dt.today()
        return today > self.disqualified_until

    @property
    def reason_description(self) -> str | None:
        """Get the reason description."""
        if self.reason:
            return self.reason.get("description")
        return None

    @property
    def reason_act(self) -> str | None:
        """Get the act under which disqualification was made."""
        if self.reason:
            return self.reason.get("act")
        return None

    @property
    def duration_years(self) -> float:
        """Calculate the duration of disqualification in years."""
        delta = self.disqualified_until - self.disqualified_from
        return delta.days / 365.25


class DisqualificationItem(BaseModel):
    """Individual disqualification item in search results."""

    # Natural person officer details
    forename: str | None = Field(None, description="Officer's first name")
    surname: str | None = Field(None, description="Officer's surname")
    title: str | None = Field(None, description="Officer's title")
    other_forenames: str | None = Field(None, description="Other forenames")

    # Corporate officer details
    company_name: str | None = Field(None, description="Corporate officer company name")
    company_number: str | None = Field(None, description="Corporate officer company number")

    # Date of birth (privacy-compliant)
    date_of_birth: str | None = Field(
        None,
        description="Date of birth (usually year only for privacy)"
    )

    # Disqualification details
    disqualifications: list[Disqualification] = Field(
        default_factory=list,
        description="List of disqualifications"
    )

    # Permissions to act
    permissions_to_act: list[dict] | None = Field(
        None,
        description="Permissions to act despite disqualification"
    )

    # Address
    address: Address | None = Field(None, description="Officer's address")

    # Links
    links: dict | None = Field(None, description="API links for related resources")

    @property
    def full_name(self) -> str:
        """Get the full name of the officer (natural or corporate)."""
        # For corporate officers
        if self.company_name:
            return self.company_name

        # For natural persons
        parts = []
        if self.title:
            parts.append(self.title)
        if self.forename:
            parts.append(self.forename)
        if self.other_forenames:
            parts.append(self.other_forenames)
        if self.surname:
            parts.append(self.surname)
        return " ".join(parts)

    @property
    def active_disqualifications(self) -> list[Disqualification]:
        """Get list of currently active disqualifications."""
        return [d for d in self.disqualifications if d.is_active]

    @property
    def has_active_disqualifications(self) -> bool:
        """Check if officer has any active disqualifications."""
        return len(self.active_disqualifications) > 0


class DisqualificationList(BaseModel):
    """List of disqualified officers."""

    items: list[DisqualificationItem] = Field(
        default_factory=list,
        description="List of disqualified officers"
    )

    # Pagination metadata
    items_per_page: int | None = Field(None, description="Number of items per page")
    start_index: int | None = Field(None, description="Starting index for pagination")
    total_results: int | None = Field(None, description="Total number of results")

    # Additional metadata
    kind: str | None = Field(None, description="Type of resource")

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
