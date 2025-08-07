"""Endpoint methods for AsyncClient - search and company operations."""

import asyncio
import random
from collections.abc import AsyncGenerator, Callable
from typing import Any

import structlog

from .exceptions import RateLimitError, ServerError
from .models import Address, Company
from .models.search import AllSearchResult, CompanySearchResult, OfficerSearchResult

logger = structlog.get_logger(__name__)


class EndpointMixin:
    """Mixin class providing endpoint methods for AsyncClient."""

    async def search_companies(
        self,
        query: str,
        items_per_page: int = 20,
        start_index: int = 0,
    ) -> CompanySearchResult:
        """Search for companies by name or number.

        Args:
            query: Search query string
            items_per_page: Number of results per page (max 100)
            start_index: Starting index for pagination

        Returns:
            CompanySearchResult with matching companies
        """
        params = {
            "q": query,
            "items_per_page": min(items_per_page, 100),
            "start_index": start_index,
        }

        response = await self.get("/search/companies", params=params)
        return CompanySearchResult(**response)

    async def search_officers(
        self,
        query: str,
        items_per_page: int = 20,
        start_index: int = 0,
    ) -> OfficerSearchResult:
        """Search for officers by name.

        Args:
            query: Search query string
            items_per_page: Number of results per page (max 100)
            start_index: Starting index for pagination

        Returns:
            OfficerSearchResult with matching officers
        """
        params = {
            "q": query,
            "items_per_page": min(items_per_page, 100),
            "start_index": start_index,
        }

        response = await self.get("/search/officers", params=params)
        return OfficerSearchResult(**response)

    async def search_all(
        self,
        query: str,
        items_per_page: int = 20,
        start_index: int = 0,
    ) -> AllSearchResult:
        """Search across all resources (companies, officers, disqualified officers).

        Args:
            query: Search query string
            items_per_page: Number of results per page (max 100)
            start_index: Starting index for pagination

        Returns:
            AllSearchResult with all matching items
        """
        params = {
            "q": query,
            "items_per_page": min(items_per_page, 100),
            "start_index": start_index,
        }

        response = await self.get("/search", params=params)
        return AllSearchResult(**response)

    async def search_all_pages(
        self,
        query: str,
        per_page: int = 20,
        max_pages: int | None = None,
    ) -> AsyncGenerator[AllSearchResult, None]:
        """Search all resources and yield results page by page.

        Args:
            query: Search query string
            per_page: Number of results per page (max 100)
            max_pages: Maximum number of pages to fetch (None for all)

        Yields:
            AllSearchResult for each page of results
        """
        start_index = 0
        page_count = 0
        items_per_page = min(per_page, 100)

        while True:
            # Check if we've reached the max pages limit
            if max_pages and page_count >= max_pages:
                break

            # Fetch the current page
            result = await self.search_all(query, items_per_page, start_index)
            yield result

            page_count += 1

            # Check if there are more pages
            if not result.has_more_pages:
                break

            # Update start index for next page
            start_index = result.next_start_index

            # Small delay between pages to be respectful
            await asyncio.sleep(0.1)

    async def get_company(self, company_number: str) -> Company:
        """Get company profile information.

        Args:
            company_number: Company registration number

        Returns:
            Company profile information

        Raises:
            ValidationError: If company number is invalid
            NotFoundError: If company doesn't exist
        """
        # Validate and normalize company number
        normalized = self.validate_company_number(company_number)

        response = await self.get(f"/company/{normalized}")
        return Company(**response)

    async def get_company_address(self, company_number: str) -> Address:
        """Get company registered office address.

        Args:
            company_number: Company registration number

        Returns:
            Registered office address

        Raises:
            ValidationError: If company number is invalid
            NotFoundError: If company doesn't exist
        """
        # Validate and normalize company number
        normalized = self.validate_company_number(company_number)

        response = await self.get(f"/company/{normalized}/registered-office-address")
        return Address(**response)

    # Convenience aliases
    async def profile(self, company_number: str) -> Company:
        """Alias for get_company."""
        return await self.get_company(company_number)

    async def address(self, company_number: str) -> Address:
        """Alias for get_company_address."""
        return await self.get_company_address(company_number)


class RetryMixin:
    """Mixin class providing retry logic for AsyncClient."""

    async def _request_with_retry(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        retry_count: int = 0,
        on_retry: Callable[[int, Exception], None] | None = None,
        **kwargs: Any,
    ) -> Any:
        """Make an HTTP request with retry logic.

        Args:
            method: HTTP method
            path: API endpoint path
            params: Query parameters
            json: JSON body data
            retry_count: Current retry attempt (for recursion)
            on_retry: Optional callback for retry events
            **kwargs: Additional arguments

        Returns:
            HTTP response object
        """
        try:
            # Call the original _request method
            return await self._request_without_retry(
                method, path, params=params, json=json, **kwargs
            )
        except RateLimitError as e:
            # Check if we should retry
            if retry_count >= self.config.max_retries:
                logger.warning(
                    "Max retries exceeded",
                    retry_count=retry_count,
                    max_retries=self.config.max_retries,
                )
                raise

            # Calculate backoff time
            if e.retry_after:
                # Use the server-provided retry time
                wait_time = e.retry_after
            else:
                # Exponential backoff with jitter
                base_wait = 2**retry_count
                jitter = random.uniform(0, 1)
                wait_time = base_wait + jitter

            logger.info(
                "Rate limited, retrying",
                retry_count=retry_count + 1,
                wait_time=wait_time,
                retry_after=e.retry_after,
            )

            # Call retry callback if provided
            if on_retry:
                on_retry(retry_count + 1, e)

            # Wait before retrying
            await asyncio.sleep(wait_time)

            # Retry the request
            return await self._request_with_retry(
                method,
                path,
                params=params,
                json=json,
                retry_count=retry_count + 1,
                on_retry=on_retry,
                **kwargs,
            )
        except ServerError as e:
            # Retry on server errors (5xx) with exponential backoff
            if retry_count >= self.config.max_retries:
                logger.warning(
                    "Max retries exceeded for server error",
                    retry_count=retry_count,
                    max_retries=self.config.max_retries,
                    status_code=e.status_code,
                )
                raise

            # Exponential backoff with jitter for server errors
            base_wait = 2**retry_count
            jitter = random.uniform(0, 1)
            wait_time = min(base_wait + jitter, 30)  # Cap at 30 seconds

            logger.info(
                "Server error, retrying",
                retry_count=retry_count + 1,
                wait_time=wait_time,
                status_code=e.status_code,
            )

            # Call retry callback if provided
            if on_retry:
                on_retry(retry_count + 1, e)

            # Wait before retrying
            await asyncio.sleep(wait_time)

            # Retry the request
            return await self._request_with_retry(
                method,
                path,
                params=params,
                json=json,
                retry_count=retry_count + 1,
                on_retry=on_retry,
                **kwargs,
            )
