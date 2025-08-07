"""Models package for UK Companies API client."""

from .address import Address
from .base import BaseModel
from .rate_limit import RateLimitInfo

__all__ = ["BaseModel", "Address", "RateLimitInfo"]
