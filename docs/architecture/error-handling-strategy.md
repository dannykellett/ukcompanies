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
- **Retry Policy:** Comprehensive retry logic with exponential and fixed backoff strategies, configurable jitter, max 3 retries by default
- **Rate Limit Handling:** Automatic retry for 429 responses with intelligent wait times using X-Ratelimit-Reset headers
- **Network Error Retry:** Automatic retry for network errors (connection failures, timeouts) with same backoff logic
- **Circuit Breaker:** Not implemented in v1.0 (keeping it simple)
- **Timeout Configuration:** 30 seconds default per request, configurable on client init
- **Error Translation:** HTTP status codes mapped to specific exceptions; API error messages preserved in exception details; Complete rate limit metadata extracted and included in `RateLimitError`

### Business Logic Errors
- **Custom Exceptions:** InvalidCompanyNumberError, InvalidDateRangeError, PaginationError
- **User-Facing Errors:** Clear messages explaining what went wrong and how to fix it
- **Error Codes:** Use HTTP status codes as base, with sub-codes for specific scenarios

### Data Consistency
- **Transaction Strategy:** N/A - SDK is stateless, no transactions needed
- **Compensation Logic:** N/A - Read-only API, no modifications to rollback
- **Idempotency:** All operations are idempotent (GET requests only)

## Retry Implementation

### RetryConfig
Configurable retry behavior with the following parameters:
- `auto_retry`: Enable/disable automatic retry (default: True)
- `max_retries`: Maximum retry attempts (default: 3)
- `backoff`: Strategy - "exponential" or "fixed" (default: "exponential")
- `base_delay`: Base delay in seconds (default: 1.0)
- `max_delay`: Maximum delay cap (default: 60.0)
- `jitter_range`: Random jitter range (default: 1.0)
- `on_retry`: Optional callback for retry events

### RetryManager
Core retry logic implementation:
- **Exponential Backoff:** `delay = min(2^attempt * base_delay, max_delay) + jitter`
- **Fixed Backoff:** `delay = base_delay + jitter`
- **Header Parsing:** Extracts `X-Ratelimit-Reset` timestamp for intelligent wait times
- **Non-blocking:** Uses `asyncio.sleep()` to maintain async behavior
- **Exception Handling:** Catches `RateLimitError` and `NetworkError` for retry logic

### Integration
- **AsyncClient:** Automatic integration with retry manager when retry is enabled
- **Error Flow:** Rate limit exceptions include complete metadata for retry decisions
- **Callback Support:** Both async and sync callbacks supported with graceful error handling