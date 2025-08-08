# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.6.0] - 2025-08-08

### Added
- Retry logic with exponential and fixed backoff strategies (Story 1.6)
- Configurable retry parameters (auto_retry, max_retries, backoff, base_delay, max_delay, jitter_range)
- Optional on_retry callback for monitoring retry attempts
- Enhanced RateLimitError with complete rate limit metadata
- X-Ratelimit-Reset header parsing for intelligent wait times
- Network error handling with automatic retry
- Non-blocking async retry behavior maintained throughout retry process

### Changed
- RateLimitError now includes rate_limit_remain, rate_limit_limit, and rate_limit_reset attributes
- AsyncClient automatically retries 429 responses when auto_retry is enabled

## [0.5.0] - 2025-01-08

### Added
- Filing history endpoint with pagination support (Story 1.5)
- Filing transaction details endpoint
- Document metadata retrieval endpoint
- Document content download with multiple format support (PDF, XHTML, JSON, CSV)
- FilingHistory and Document models with comprehensive validation
- Async generator support for paginated filing history
- Binary content handling for PDF documents
- Streaming support for large documents

## [0.4.0] - 2025-01-07

### Added
- Officers endpoint for listing company officers
- Officer appointments endpoint
- Disqualified officers check endpoint
- Persons with significant control (PSC) endpoints
- Insolvency details endpoint
- Company charges endpoint
- Comprehensive officer and PSC models

## [0.3.0] - 2025-01-06

### Added
- Search endpoints for companies and officers (Story 1.3)
- Combined search_all endpoint with pagination
- Company profile endpoint
- Registered office address endpoint
- Search result models with pagination support
- Company and address models

## [0.2.0] - 2025-01-05

### Added
- Core AsyncClient with httpx integration (Story 1.2)
- HTTP Basic Auth with API key authentication
- Base Pydantic models for response validation
- Custom exception hierarchy (CompaniesHouseError, AuthenticationError, RateLimitError, etc.)
- Rate limit information extraction from headers
- Configuration module with constants
- Comprehensive unit test structure with respx mocking

## [0.1.0] - 2025-08-08

### Added
- Initial project setup with uv package manager (Story 1.1)
- Core AsyncClient with httpx integration (Story 1.2)
- Search endpoints for companies and officers (Story 1.3)
- Officer and appointments endpoints (Story 1.4)
- Filing history and document endpoints (Story 1.5)
- Comprehensive retry logic and rate limiting (Story 1.6)
- PyPI package publication (Story 2.1)
- Production-ready Python SDK with full Companies House API coverage
- Async-first architecture with context manager support
- Type-safe Pydantic models for all API responses
- Intelligent retry logic with exponential backoff
- Rate limit awareness with X-Ratelimit-Reset header parsing
- Comprehensive test suite (323 tests) with mock and live API validation
- Complete documentation with MkDocs
- CLI interface for command-line usage