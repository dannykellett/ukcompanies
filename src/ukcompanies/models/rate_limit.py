"""Rate limit information model."""

from datetime import datetime

from pydantic import Field

from .base import BaseModel


class RateLimitInfo(BaseModel):
    """Rate limit information from API responses."""

    remain: int = Field(..., description="Remaining requests in current window")
    limit: int = Field(..., description="Total requests allowed in window")
    reset: datetime = Field(..., description="When the rate limit window resets")
    retry_after: int | None = Field(None, description="Seconds to wait if rate limited")

    @property
    def is_limited(self) -> bool:
        """Check if currently rate limited.

        Returns:
            True if rate limited (no remaining requests)
        """
        return self.remain <= 0

    @property
    def percent_remaining(self) -> float:
        """Calculate percentage of rate limit remaining.

        Returns:
            Percentage of requests remaining (0.0 to 100.0)
        """
        if self.limit == 0:
            return 0.0
        return (self.remain / self.limit) * 100.0

    @property
    def seconds_until_reset(self) -> float:
        """Calculate seconds until rate limit resets.

        Returns:
            Seconds until reset (negative if reset time has passed)
        """
        now = datetime.now(self.reset.tzinfo)
        delta = self.reset - now
        return delta.total_seconds()
