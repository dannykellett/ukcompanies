"""Endpoint methods for AsyncClient - search and company operations."""

import asyncio
import random
from collections.abc import AsyncGenerator, Callable
from typing import Any

import structlog

from .exceptions import RateLimitError, ServerError, ValidationError
from .models import Address, Company
from .models.appointment import AppointmentList
from .models.disqualification import DisqualificationList
from .models.document import Document, DocumentContent, DocumentFormat, DocumentMetadata
from .models.filing import FilingCategory, FilingHistoryList, FilingTransaction
from .models.officer import OfficerList
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

    async def get_officers(
        self,
        company_number: str,
        items_per_page: int = 35,
        start_index: int = 0,
        register_type: str | None = None,
        order_by: str | None = None,
    ) -> OfficerList:
        """Get list of officers for a company.

        Args:
            company_number: Company registration number
            items_per_page: Number of items per page (max 50)
            start_index: Starting index for pagination
            register_type: Type of register (directors, secretaries, llp-members)
            order_by: Field to order by (appointed_on, resigned_on, surname)

        Returns:
            OfficerList with company officers

        Raises:
            ValidationError: If company number is invalid
            NotFoundError: If company doesn't exist
        """
        # Validate and normalize company number
        normalized = self.validate_company_number(company_number)

        params = {
            "items_per_page": min(items_per_page, 50),
            "start_index": start_index,
        }

        if register_type:
            params["register_type"] = register_type
        if order_by:
            params["order_by"] = order_by

        response = await self.get(f"/company/{normalized}/officers", params=params)
        return OfficerList(**response)

    async def get_appointments(
        self,
        officer_id: str,
        items_per_page: int = 50,
        start_index: int = 0,
    ) -> AppointmentList:
        """Get all appointments for a specific officer.

        Args:
            officer_id: Unique officer identifier
            items_per_page: Number of items per page (max 50)
            start_index: Starting index for pagination

        Returns:
            AppointmentList with all officer appointments

        Raises:
            ValidationError: If officer ID is invalid
            NotFoundError: If officer doesn't exist
        """
        # Validate officer ID
        if not officer_id or not officer_id.strip():
            raise ValidationError("Officer ID cannot be empty")

        # Clean the officer ID
        clean_id = officer_id.strip()

        params = {
            "items_per_page": min(items_per_page, 50),
            "start_index": start_index,
        }

        response = await self.get(f"/officers/{clean_id}/appointments", params=params)
        return AppointmentList(**response)

    async def get_disqualified_natural(
        self, officer_id: str
    ) -> DisqualificationList:
        """Get disqualification details for a natural person.

        Args:
            officer_id: Unique officer identifier

        Returns:
            DisqualificationList with disqualification details

        Raises:
            ValidationError: If officer ID is invalid
            NotFoundError: If officer doesn't exist or has no disqualifications
        """
        # Validate officer ID
        if not officer_id or not officer_id.strip():
            raise ValidationError("Officer ID cannot be empty")

        # Clean the officer ID
        clean_id = officer_id.strip()

        response = await self.get(f"/disqualified-officers/natural/{clean_id}")
        return DisqualificationList(**response)

    async def get_disqualified_corporate(
        self, officer_id: str
    ) -> DisqualificationList:
        """Get disqualification details for a corporate officer.

        Args:
            officer_id: Unique officer identifier

        Returns:
            DisqualificationList with disqualification details

        Raises:
            ValidationError: If officer ID is invalid
            NotFoundError: If officer doesn't exist or has no disqualifications
        """
        # Validate officer ID
        if not officer_id or not officer_id.strip():
            raise ValidationError("Officer ID cannot be empty")

        # Clean the officer ID
        clean_id = officer_id.strip()

        response = await self.get(f"/disqualified-officers/corporate/{clean_id}")
        return DisqualificationList(**response)

    async def get_appointments_pages(
        self,
        officer_id: str,
        per_page: int = 50,
        max_pages: int | None = None,
    ) -> AsyncGenerator[AppointmentList, None]:
        """Get all appointments for an officer, yielding page by page.

        Args:
            officer_id: Unique officer identifier
            per_page: Number of results per page (max 50)
            max_pages: Maximum number of pages to fetch (None for all)

        Yields:
            AppointmentList for each page of results
        """
        start_index = 0
        page_count = 0
        items_per_page = min(per_page, 50)

        while True:
            # Check if we've reached the max pages limit
            if max_pages and page_count >= max_pages:
                break

            # Fetch the current page
            result = await self.get_appointments(officer_id, items_per_page, start_index)
            yield result

            page_count += 1

            # Check if there are more pages
            if not result.has_more_pages:
                break

            # Update start index for next page
            start_index = result.next_start_index

            # Small delay between pages to be respectful
            await asyncio.sleep(0.1)

    # Convenience aliases
    async def profile(self, company_number: str) -> Company:
        """Alias for get_company."""
        return await self.get_company(company_number)

    async def address(self, company_number: str) -> Address:
        """Alias for get_company_address."""
        return await self.get_company_address(company_number)

    async def officers(self, company_number: str, **kwargs: Any) -> OfficerList:
        """Alias for get_officers."""
        return await self.get_officers(company_number, **kwargs)

    async def appointments(self, officer_id: str, **kwargs: Any) -> AppointmentList:
        """Alias for get_appointments."""
        return await self.get_appointments(officer_id, **kwargs)

    async def disqualified(self, officer_id: str, corporate: bool = False) -> DisqualificationList:
        """Get disqualification details for an officer.

        Args:
            officer_id: Unique officer identifier
            corporate: Whether this is a corporate officer

        Returns:
            DisqualificationList with disqualification details
        """
        if corporate:
            return await self.get_disqualified_corporate(officer_id)
        else:
            return await self.get_disqualified_natural(officer_id)

    async def filing_history(
        self,
        company_number: str,
        category: FilingCategory | str | None = None,
        items_per_page: int = 25,
        start_index: int = 0,
    ) -> FilingHistoryList:
        """Get filing history for a company.

        Args:
            company_number: Company registration number
            category: Optional filing category filter
            items_per_page: Number of items per page (max 100)
            start_index: Starting index for pagination

        Returns:
            FilingHistoryList with filing history items

        Raises:
            ValidationError: If company number is invalid
            NotFoundError: If company doesn't exist
        """
        # Validate and normalize company number
        normalized = self.validate_company_number(company_number)

        params = {
            "items_per_page": min(items_per_page, 100),
            "start_index": start_index,
        }

        # Add category filter if provided
        if category:
            # Convert enum to string if needed
            if isinstance(category, FilingCategory):
                params["category"] = category.value
            else:
                params["category"] = category

        response = await self.get(f"/company/{normalized}/filing-history", params=params)
        return FilingHistoryList(**response)

    async def filing_transaction(
        self,
        company_number: str,
        transaction_id: str,
    ) -> FilingTransaction:
        """Get details of a specific filing transaction.

        Args:
            company_number: Company registration number
            transaction_id: Unique filing transaction identifier

        Returns:
            FilingTransaction with detailed filing information

        Raises:
            ValidationError: If company number or transaction ID is invalid
            NotFoundError: If company or transaction doesn't exist
        """
        # Validate and normalize company number
        normalized = self.validate_company_number(company_number)

        # Validate transaction ID
        if not transaction_id or not transaction_id.strip():
            raise ValidationError("Transaction ID cannot be empty")

        clean_id = transaction_id.strip()

        response = await self.get(f"/company/{normalized}/filing-history/{clean_id}")
        return FilingTransaction(**response)

    async def document(self, document_id: str) -> Document:
        """Get document metadata.

        Args:
            document_id: Unique document identifier

        Returns:
            Document with metadata and available formats

        Raises:
            ValidationError: If document ID is invalid
            NotFoundError: If document doesn't exist
        """
        # Validate document ID
        if not document_id or not document_id.strip():
            raise ValidationError("Document ID cannot be empty")

        clean_id = document_id.strip()

        response = await self.get(f"/document/{clean_id}")

        # Parse response to DocumentMetadata first
        metadata = DocumentMetadata(**response)

        # Convert to Document model
        return Document.from_metadata(clean_id, metadata)

    async def document_content(
        self,
        document_id: str,
        format: DocumentFormat | str | None = None,
    ) -> DocumentContent:
        """Get document content in specified format.

        Args:
            document_id: Unique document identifier
            format: Desired document format (PDF, XHTML, JSON, etc.)

        Returns:
            DocumentContent with actual document data

        Raises:
            ValidationError: If document ID is invalid
            NotFoundError: If document doesn't exist
        """
        # Validate document ID
        if not document_id or not document_id.strip():
            raise ValidationError("Document ID cannot be empty")

        clean_id = document_id.strip()

        # Set Accept header based on format
        headers = {}
        if format:
            # Convert enum to string if needed
            if isinstance(format, DocumentFormat):
                headers["Accept"] = format.value
            else:
                headers["Accept"] = format

        # Make the request directly with _request to handle binary content
        response = await self._request(
            "GET",
            f"/document/{clean_id}/content",
            headers=headers,
        )

        # Extract content based on content type
        content_type = response.headers.get("content-type", "")

        # Create DocumentContent based on response type
        if "application/pdf" in content_type:
            # Binary content for PDFs
            return DocumentContent(
                document_id=clean_id,
                content_type=DocumentFormat.PDF,
                content=response.content,
                content_length=len(response.content),
                etag=response.headers.get("etag"),
            )
        elif "application/json" in content_type:
            # JSON content
            return DocumentContent(
                document_id=clean_id,
                content_type=DocumentFormat.JSON,
                text_content=response.text,
                content_length=len(response.text),
                etag=response.headers.get("etag"),
            )
        elif "text/csv" in content_type:
            # CSV content
            return DocumentContent(
                document_id=clean_id,
                content_type=DocumentFormat.CSV,
                text_content=response.text,
                content_length=len(response.text),
                etag=response.headers.get("etag"),
            )
        elif "application/xhtml" in content_type or "text/html" in content_type:
            # XHTML/HTML content
            return DocumentContent(
                document_id=clean_id,
                content_type=DocumentFormat.XHTML,
                text_content=response.text,
                content_length=len(response.text),
                etag=response.headers.get("etag"),
            )
        else:
            # Default to text content
            return DocumentContent(
                document_id=clean_id,
                content_type=DocumentFormat.XML if "xml" in content_type else DocumentFormat.XHTML,
                text_content=response.text,
                content_length=len(response.text),
                etag=response.headers.get("etag"),
            )

    async def filing_history_pages(
        self,
        company_number: str,
        category: FilingCategory | str | None = None,
        per_page: int = 25,
        max_pages: int | None = None,
    ) -> AsyncGenerator[FilingHistoryList, None]:
        """Get filing history for a company, yielding page by page.

        Args:
            company_number: Company registration number
            category: Optional filing category filter
            per_page: Number of results per page (max 100)
            max_pages: Maximum number of pages to fetch (None for all)

        Yields:
            FilingHistoryList for each page of results
        """
        start_index = 0
        page_count = 0
        items_per_page = min(per_page, 100)

        while True:
            # Check if we've reached the max pages limit
            if max_pages and page_count >= max_pages:
                break

            # Fetch the current page
            result = await self.filing_history(
                company_number, category, items_per_page, start_index
            )
            yield result

            page_count += 1

            # Check if there are more pages
            total_items = result.total_count
            fetched_items = start_index + len(result.items)

            if fetched_items >= total_items:
                break

            # Update start index for next page
            start_index = fetched_items

            # Small delay between pages to be respectful
            await asyncio.sleep(0.1)


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
