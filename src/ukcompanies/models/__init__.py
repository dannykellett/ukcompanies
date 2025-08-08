"""Models package for UK Companies API client."""

from .address import Address
from .appointment import Appointment, AppointmentList
from .appointment import CompanyStatus as AppointmentCompanyStatus
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
from .disqualification import (
    Disqualification,
    DisqualificationItem,
    DisqualificationList,
    DisqualificationReason,
)
from .officer import (
    IdentificationType,
    Officer,
    OfficerList,
    OfficerRole,
    PartialDate,
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
    # Officer
    "Officer",
    "OfficerList",
    "OfficerRole",
    "IdentificationType",
    "PartialDate",
    # Appointment
    "Appointment",
    "AppointmentList",
    "AppointmentCompanyStatus",
    # Disqualification
    "Disqualification",
    "DisqualificationItem",
    "DisqualificationList",
    "DisqualificationReason",
    # Search
    "SearchResult",
    "CompanySearchResult",
    "OfficerSearchResult",
    "AllSearchResult",
    "CompanySearchItem",
    "OfficerSearchItem",
    "DisqualifiedOfficerSearchItem",
]
