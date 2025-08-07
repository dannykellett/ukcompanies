"""UK Companies House API SDK."""

from .auth import AuthHandler
from .client import AsyncClient
from .config import Config
from .exceptions import (
    AuthenticationError,
    CompaniesHouseError,
    NetworkError,
    NotFoundError,
    RateLimitError,
    ServerError,
    ValidationError,
)
from .models import (
    Address,
    BaseModel,
    Company,
    CompanySearchResult,
    OfficerSearchResult,
    RateLimitInfo,
)

__version__ = "0.1.0"

__all__ = [
    "__version__",
    # Client
    "AsyncClient",
    "Config",
    "AuthHandler",
    # Models
    "BaseModel",
    "Address",
    "Company",
    "CompanySearchResult",
    "OfficerSearchResult",
    "RateLimitInfo",
    # Exceptions
    "CompaniesHouseError",
    "AuthenticationError",
    "RateLimitError",
    "NotFoundError",
    "ValidationError",
    "ServerError",
    "NetworkError",
]
