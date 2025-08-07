# Requirements

## Functional
- Must support all documented Companies House endpoints listed above
- Authentication via HTTP Basic Auth using API key as username
- Should allow API key via env var (`COMPANIES_HOUSE_API_KEY`) or constructor
- Must model responses with `pydantic.BaseModel`
- Should provide CLI for basic company search
- Implement pagination logic for `search_all`
- Must support built-in rate-limit retry logic (configurable)

## Non-Functional
- Use Python 3.10+ features (e.g., `x | y` syntax)
- Must use `uv` as the package manager
- All endpoints must be covered by tests using `pytest` + `respx`
- Maintain 100% test coverage
- Follow `ruff` linting/formatting standards
- Package must be installable via PyPI
- Include full documentation and usage examples

## Rate Limiting & Monitoring
- Track `X-Ratelimit-Remain` and log when low
- Use `X-Ratelimit-Reset` for retry wait time
- Raise `RateLimitError` on 429 with retry metadata
- Expose retry info and allow opt-in debug logs
- Document all rate-limiting features in README