# External APIs

## Companies House API
- **Purpose:** Official UK government API providing access to company registration data, officer information, filing history, and other corporate records
- **Documentation:** https://developer.company-information.service.gov.uk/
- **Base URL(s):** 
  - Production: `https://api.company-information.service.gov.uk`
  - Sandbox: `https://api-sandbox.company-information.service.gov.uk` (for testing)
- **Authentication:** HTTP Basic Auth with API key as username, empty password
- **Rate Limits:** 600 requests per 5-minute window (per API key)

**Key Endpoints Used:**
- `GET /search/companies` - Search for companies by name
- `GET /search/officers` - Search for officers by name  
- `GET /search` - Search all (companies, officers, disqualified officers)
- `GET /company/{company_number}` - Get company profile
- `GET /company/{company_number}/officers` - List company officers
- `GET /company/{company_number}/filing-history` - Get filing history
- `GET /company/{company_number}/charges` - Get charges
- `GET /company/{company_number}/insolvency` - Get insolvency details
- `GET /company/{company_number}/registered-office-address` - Get registered address
- `GET /company/{company_number}/persons-with-significant-control` - List PSCs
- `GET /officers/{officer_id}/appointments` - Get officer appointments
- `GET /disqualified-officers/natural/{officer_id}` - Check disqualification
- `GET /document/{document_id}` - Retrieve document metadata

**Integration Notes:** 
- API returns JSON responses that map directly to our Pydantic models
- Rate limit headers (`X-Ratelimit-Remain`, `X-Ratelimit-Limit`, `X-Ratelimit-Reset`) must be parsed for retry logic
- 429 responses trigger exponential backoff retry mechanism
- Some endpoints have different rate limits or require additional permissions
- Sandbox environment available for testing without affecting rate limits
- No webhook support - all interactions are request/response
- API is not versioned, must handle potential breaking changes gracefully