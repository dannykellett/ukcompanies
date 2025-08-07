"""Models package for UK Companies API client."""

from .address import Address
from .base import BaseModel
from .company import (
    AccountingReference,
    Accounts,
    Company,
    CompanyStatus,
    CompanyType,
    ConfirmationStatement,
    Jurisdiction,
)
from .rate_limit import RateLimitInfo
from .search import (
    AllSearchResult,
    CompanySearchItem,
    CompanySearchResult,
    DisqualifiedOfficerSearchItem,
    OfficerSearchItem,
    OfficerSearchResult,
    SearchResult,
)

__all__ = [
    # Base
    "BaseModel",
    "Address",
    "RateLimitInfo",
    # Company
    "Company",
    "CompanyStatus",
    "CompanyType",
    "Jurisdiction",
    "AccountingReference",
    "ConfirmationStatement",
    "Accounts",
    # Search
    "SearchResult",
    "CompanySearchResult",
    "OfficerSearchResult",
    "AllSearchResult",
    "CompanySearchItem",
    "OfficerSearchItem",
    "DisqualifiedOfficerSearchItem",
]
