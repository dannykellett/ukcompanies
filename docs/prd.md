# Product Requirements Document: `ukcompanies`

## Title & Overview

**Title**: `ukcompanies` — Async Python SDK for Companies House API

**Overview**:
`ukcompanies` is a modern, production-ready Python package that serves as a full-featured asynchronous wrapper for the UK Companies House API. Designed with developer experience and performance in mind, the package leverages modern Python tooling and idioms to simplify access to official UK company data for developers, analysts, and integrators.

This SDK aims for near-parity with the established `chwrapper` package while introducing async capabilities, improved models, robust testing, and thoughtful error handling out of the box.

---

## Goals

- Provide a fully async interface to the Companies House API
- Match or exceed the functionality of the `chwrapper` package
- Model all key API responses using Pydantic
- Ensure authentication via env var and constructor
- Include extensive test coverage and CI-compatible testing
- Deliver clean, modern developer experience with uv, httpx, ruff

---

## User Personas

1. **Python Developers** – Internal tooling or API integration use.
2. **Data Engineers & Analysts** – Ingesting and analyzing Companies House data.
3. **LegalTech and RegTech Engineers** – KYB/compliance pipelines.
4. **Open Source Contributors** – SDK enhancement and usage documentation.

---

## Features

### Core Client Features
- Fully async client powered by `httpx.AsyncClient`
- API key authentication via env var or constructor
- Configurable base URL (for sandbox or mocks)
- Informative error handling with custom exceptions
- Built-in rate-limit awareness via headers

### Endpoint Coverage
- `search_companies(term)`
- `search_officers(term)`
- `appointments(officer_id)`
- `address(company_number)`
- `profile(company_number)`
- `insolvency(company_number)`
- `filing_history(company_number, transaction)`
- `charges(company_number, charge_id)`
- `officers(company_number)`
- `disqualified(officer_id)`
- `persons_significant_control(company_number)`
- `significant_control(company_number, entity_id)`
- `document(document_id)`
- `search_all(term, per_page, max_pages)`

### Retry Logic (New)
- Optional automatic retry for rate-limited requests (`429`)
- Configurable parameters:
  - `auto_retry`: Enable/disable automatic retries
  - `max_retries`: Max retry attempts
  - `backoff`: Strategy (`"exponential"` or `"fixed"`)
  - `on_retry`: Optional callback for logging
- Respects `X-Ratelimit-Reset` for accurate delay between retries

### Developer Experience
- Modern toolchain: `uv`, `ruff`, `pydantic`, `respx`
- Typed response models
- Full pytest + respx test suite
- Example usage and CLI entry point (`python -m ukcompanies search ...`)

---

## Requirements

### Functional
- Must support all documented Companies House endpoints listed above
- Authentication via HTTP Basic Auth using API key as username
- Should allow API key via env var (`COMPANIES_HOUSE_API_KEY`) or constructor
- Must model responses with `pydantic.BaseModel`
- Should provide CLI for basic company search
- Implement pagination logic for `search_all`
- Must support built-in rate-limit retry logic (configurable)

### Non-Functional
- Use Python 3.10+ features (e.g., `x | y` syntax)
- Must use `uv` as the package manager
- All endpoints must be covered by tests using `pytest` + `respx`
- Maintain 100% test coverage
- Follow `ruff` linting/formatting standards
- Package must be installable via PyPI
- Include full documentation and usage examples

### Rate Limiting & Monitoring
- Track `X-Ratelimit-Remain` and log when low
- Use `X-Ratelimit-Reset` for retry wait time
- Raise `RateLimitError` on 429 with retry metadata
- Expose retry info and allow opt-in debug logs
- Document all rate-limiting features in README

---

## User Experience Design Goals

- Simple and consistent async API for all endpoints
- Idiomatic Python interface using type hints and named params
- Automatic handling of auth and base headers
- Pydantic-powered responses with code completion in editors
- Clear error messages and custom exceptions for common cases
- CLI UX mirrors Python client behavior
- Zero-config experience for `.env` users; constructor override for advanced use

---

## Out of Scope

- Frontend UI components or visualizations
- Third-party integrations beyond Companies House
- Non-async versions of endpoints
- Database storage or ORM integration
- PDF/document parsing (e.g., of filing documents)

_(Built-in rate limit retry/backoff logic is now in scope as an optional client feature)_

---

## Launch Plan

### Phase 1: Internal Alpha
- Develop core client and cover all endpoints
- Implement and test authentication, retries, and rate limit handling
- Internal QA and lint/test automation

### Phase 2: Public Beta (v0.1)
- Publish package to PyPI
- Announce on GitHub with usage examples
- Gather early user feedback via issues/PRs

### Phase 3: Stable v1.0
- Finalize CLI, docs, and test coverage
- Monitor adoption and community feedback
- Add sync wrapper and optional CLI features if requested

---

## Risks and Open Questions

### Risks
- **API Changes**: Companies House API is not versioned; backward-incompatible changes could break the SDK.
- **Rate Limiting**: Unexpected rate caps from Companies House could degrade client reliability under load.
- **Async-only Approach**: Some users may lack `asyncio` context or prefer sync clients.
- **Community Engagement**: Adoption might be slow if `chwrapper` remains dominant.

### Open Questions _(Resolved)_
- ❌ Sync wrapper (`CompaniesHouseSyncClient`) will **not** be included in v1.0
- ❌ No support planned for non-Python tooling like OpenAPI specs
- ❌ No client-level caching for now to maintain simplicity
