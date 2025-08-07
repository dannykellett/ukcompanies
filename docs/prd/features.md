# Features

## Core Client Features
- Fully async client powered by `httpx.AsyncClient`
- API key authentication via env var or constructor
- Configurable base URL (for sandbox or mocks)
- Informative error handling with custom exceptions
- Built-in rate-limit awareness via headers

## Endpoint Coverage
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

## Retry Logic (New)
- Optional automatic retry for rate-limited requests (`429`)
- Configurable parameters:
  - `auto_retry`: Enable/disable automatic retries
  - `max_retries`: Max retry attempts
  - `backoff`: Strategy (`"exponential"` or `"fixed"`)
  - `on_retry`: Optional callback for logging
- Respects `X-Ratelimit-Reset` for accurate delay between retries

## Developer Experience
- Modern toolchain: `uv`, `ruff`, `pydantic`, `respx`
- Typed response models
- Full pytest + respx test suite
- Example usage and CLI entry point (`python -m ukcompanies search ...`)