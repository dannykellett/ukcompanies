# Error Handling Strategy

## General Approach
- **Error Model:** Exception-based with custom exception hierarchy inheriting from base `CompaniesHouseError`
- **Exception Hierarchy:** CompaniesHouseError → AuthenticationError, RateLimitError, NotFoundError, ValidationError, ServerError, NetworkError
- **Error Propagation:** Errors bubble up with context preservation; retry logic intercepts retryable errors

## Logging Standards
- **Library:** structlog 24.4.0
- **Format:** JSON structured logging for production, colored console for development
- **Levels:** DEBUG (detailed traces), INFO (operations), WARNING (degraded behavior), ERROR (failures)
- **Required Context:**
  - Correlation ID: UUID per client session for tracing related requests
  - Service Context: Endpoint called, method, parameters (excluding sensitive data)
  - User Context: No PII logged; only company numbers and public identifiers

## Error Handling Patterns

### External API Errors
- **Retry Policy:** Exponential backoff with jitter, max 3 retries by default, configurable via client
- **Circuit Breaker:** Not implemented in v1.0 (keeping it simple)
- **Timeout Configuration:** 30 seconds default per request, configurable on client init
- **Error Translation:** HTTP status codes mapped to specific exceptions; API error messages preserved in exception details; Rate limit headers extracted and included in `RateLimitError`

### Business Logic Errors
- **Custom Exceptions:** InvalidCompanyNumberError, InvalidDateRangeError, PaginationError
- **User-Facing Errors:** Clear messages explaining what went wrong and how to fix it
- **Error Codes:** Use HTTP status codes as base, with sub-codes for specific scenarios

### Data Consistency
- **Transaction Strategy:** N/A - SDK is stateless, no transactions needed
- **Compensation Logic:** N/A - Read-only API, no modifications to rollback
- **Idempotency:** All operations are idempotent (GET requests only)