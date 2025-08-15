# End-to-End Tests

These tests make real API calls to the Companies House API to verify the client works correctly with the live service.

## Prerequisites

You need a valid Companies House API key. Get one from:
https://developer.company-information.service.gov.uk/get-started

## Running the Tests

### Set your API key:
```bash
export COMPANIES_HOUSE_API_KEY='your-api-key-here'
```

### Run all e2e tests with pytest:
```bash
uv run pytest tests/e2e/ -v
```

### Run the test script directly:
```bash
uv run python tests/e2e/test_live_api.py
```

### Skip e2e tests when running the full test suite:
```bash
uv run pytest -m "not e2e"
```

## What the Tests Cover

- **Company Profile**: Retrieves real company data
- **Company Search**: Searches for companies by name
- **Officers**: Gets company officers/directors
- **Filing History**: Retrieves filing records
- **Rate Limiting**: Verifies rate limit header extraction
- **Error Handling**: Tests validation and not-found scenarios

## Test Data

The tests use real UK companies:
- Companies House Services Limited (03177648)
- J Sainsbury PLC (00306993)
- Search queries for well-known companies

## Rate Limits

The Companies House API has rate limits:
- 600 requests per 5 minutes for authenticated requests
- Tests extract and display rate limit information

## Notes

- Tests require internet connectivity
- Tests use real API calls (counts against rate limits)
- Some tests may fail if test companies change status