# Security

## Input Validation
- **Validation Library:** pydantic for all model validation
- **Validation Location:** At SDK boundary before any API calls
- **Required Rules:**
  - All external inputs MUST be validated
  - Validation at API boundary before processing
  - Whitelist approach preferred over blacklist

## Authentication & Authorization
- **Auth Method:** HTTP Basic Auth with API key as username
- **Session Management:** No sessions - stateless API client
- **Required Patterns:**
  - API key must be provided via environment variable or constructor
  - Never expose API key in logs or error messages
  - Validate API key format before use

## Secrets Management
- **Development:** .env file with python-dotenv (never commit .env)
- **Production:** Environment variables or secure secrets manager
- **Code Requirements:**
  - NEVER hardcode secrets
  - Access via configuration service only
  - No secrets in logs or error messages

## API Security
- **Rate Limiting:** Honor X-Ratelimit headers, implement backoff
- **CORS Policy:** N/A - SDK is client-side
- **Security Headers:** User-Agent header with SDK version for tracking
- **HTTPS Enforcement:** Only connect to https:// URLs (except localhost for testing)

## Data Protection
- **Encryption at Rest:** N/A - SDK doesn't store data
- **Encryption in Transit:** HTTPS enforced for all API calls
- **PII Handling:** Never log personal data; Only log company numbers and public identifiers; Mask/redact any PII in error messages
- **Logging Restrictions:** No API keys, personal addresses, officer personal details, or authentication headers

## Dependency Security
- **Scanning Tool:** GitHub Dependabot + pip-audit in CI
- **Update Policy:** Monthly dependency updates, immediate for security patches
- **Approval Process:** All new dependencies require justification in PR

## Security Testing
- **SAST Tool:** Bandit for Python security scanning
- **DAST Tool:** N/A - Client library doesn't expose attack surface
- **Penetration Testing:** N/A - Client library, not a service