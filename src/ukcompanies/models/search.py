"""Search result models for UK Companies API."""

from datetime import date
from typing import Any

from pydantic import Field

from .address import Address
from .base import BaseModel


class CompanySearchItem(BaseModel):
    """Company search result item."""

    company_number: str = Field(..., description="Company registration number")
    company_type: str | None = Field(None, description="Type of company")
    title: str = Field(..., description="Company name")
    company_status: str | None = Field(None, description="Company status")
    date_of_creation: date | None = Field(None, description="Date company was incorporated")
    date_of_cessation: date | None = Field(None, description="Date company ceased")
    address: Address | None = Field(None, description="Company address")
    address_snippet: str | None = Field(None, description="Formatted address string")
    description: str | None = Field(None, description="Company description")
    description_identifier: list[str] | None = Field(None, description="Description identifiers")
    matches: dict[str, list[int]] | None = Field(None, description="Search match positions")
    kind: str = Field("searchresults#company", description="Resource kind")
    links: dict[str, str] | None = Field(None, description="Related resource links")


class OfficerSearchItem(BaseModel):
    """Officer search result item."""

    title: str = Field(..., description="Officer name")
    description: str | None = Field(None, description="Officer description")
    description_identifiers: list[str] | None = Field(None, description="Description identifiers")
    appointment_count: int | None = Field(None, description="Number of appointments")
    date_of_birth: dict[str, int] | None = Field(None, description="Date of birth (month/year)")
    address: Address | None = Field(None, description="Officer address")
    address_snippet: str | None = Field(None, description="Formatted address string")
    matches: dict[str, list[int]] | None = Field(None, description="Search match positions")
    snippet: str | None = Field(None, description="Search result snippet")
    kind: str = Field("searchresults#officer", description="Resource kind")
    links: dict[str, str] | None = Field(None, description="Related resource links")


class DisqualifiedOfficerSearchItem(BaseModel):
    """Disqualified officer search result item."""

    title: str = Field(..., description="Officer name")
    description: str | None = Field(None, description="Officer description")
    date_of_birth: dict[str, int] | None = Field(None, description="Date of birth (month/year)")
    address: Address | None = Field(None, description="Officer address")
    address_snippet: str | None = Field(None, description="Formatted address string")
    matches: dict[str, list[int]] | None = Field(None, description="Search match positions")
    snippet: str | None = Field(None, description="Search result snippet")
    kind: str = Field("searchresults#disqualified-officer", description="Resource kind")
    links: dict[str, str] | None = Field(None, description="Related resource links")


class SearchResult(BaseModel):
    """Base search result with pagination."""

    items: list[Any] = Field(default_factory=list, description="Search result items")
    items_per_page: int = Field(20, description="Number of items per page")
    kind: str = Field(..., description="Type of search results")
    page_number: int = Field(1, description="Current page number")
    start_index: int = Field(0, description="Starting index")
    total_results: int = Field(0, description="Total number of results")

    @property
    def has_more_pages(self) -> bool:
        """Check if there are more pages available."""
        return self.start_index + self.items_per_page < self.total_results

    @property
    def next_start_index(self) -> int:
        """Get the start index for the next page."""
        return self.start_index + self.items_per_page

    @property
    def total_pages(self) -> int:
        """Calculate total number of pages."""
        if self.items_per_page == 0:
            return 0
        return (self.total_results + self.items_per_page - 1) // self.items_per_page


class CompanySearchResult(SearchResult):
    """Company search results."""

    items: list[CompanySearchItem] = Field(default_factory=list, description="Company search items")
    kind: str = Field("search#companies", description="Search result type")


class OfficerSearchResult(SearchResult):
    """Officer search results."""

    items: list[OfficerSearchItem] = Field(default_factory=list, description="Officer search items")
    kind: str = Field("search#officers", description="Search result type")


class AllSearchResult(SearchResult):
    """Combined search results for all types."""

    items: list[CompanySearchItem | OfficerSearchItem | DisqualifiedOfficerSearchItem] = Field(
        default_factory=list, description="All search items"
    )
    kind: str = Field("search#all", description="Search result type")

    def get_companies(self) -> list[CompanySearchItem]:
        """Get only company items from results."""
        return [item for item in self.items if isinstance(item, CompanySearchItem)]

    def get_officers(self) -> list[OfficerSearchItem]:
        """Get only officer items from results."""
        return [item for item in self.items if isinstance(item, OfficerSearchItem)]

    def get_disqualified_officers(self) -> list[DisqualifiedOfficerSearchItem]:
        """Get only disqualified officer items from results."""
        return [item for item in self.items if isinstance(item, DisqualifiedOfficerSearchItem)]
