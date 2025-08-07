# Test Strategy and Standards

## Testing Philosophy
- **Approach:** Test-after development with comprehensive coverage (TDD optional for complex logic)
- **Coverage Goals:** 100% code coverage as specified in PRD
- **Test Pyramid:** 60% unit tests, 30% integration tests, 10% e2e tests

## Test Types and Organization

### Unit Tests
- **Framework:** pytest 8.3.0 with pytest-asyncio
- **File Convention:** `test_[module_name].py` in tests/unit/
- **Location:** tests/unit/ mirroring src structure
- **Mocking Library:** unittest.mock for Python objects, respx for HTTP
- **Coverage Requirement:** 100% of business logic

**AI Agent Requirements:**
- Generate tests for all public methods
- Cover edge cases and error conditions
- Follow AAA pattern (Arrange, Act, Assert)
- Mock all external dependencies

### Integration Tests
- **Scope:** Service methods with mocked HTTP responses
- **Location:** tests/integration/
- **Test Infrastructure:**
  - **Companies House API:** respx for complete HTTP mocking
  - **Rate Limiting:** Mock rate limit headers and 429 responses
  - **Authentication:** Test with valid/invalid API keys
  - **Pagination:** Test multi-page result handling

### End-to-End Tests
- **Framework:** pytest with real API calls to sandbox
- **Scope:** Critical user journeys against Companies House sandbox API
- **Environment:** Optional, only run with `--e2e` flag
- **Test Data:** Use known test companies in sandbox environment

## Test Data Management
- **Strategy:** Fixture-based with JSON response samples
- **Fixtures:** tests/fixtures/ with real API response examples
- **Factories:** Pydantic model factories for generating test data
- **Cleanup:** Not needed - all tests use mocks or read-only sandbox API

## Continuous Testing
- **CI Integration:** Run on every push and PR via GitHub Actions; Test matrix: Python 3.10, 3.11, 3.12; Fail if coverage drops below 100%
- **Performance Tests:** Basic timing assertions for retry logic
- **Security Tests:** Ensure no API keys in logs, validate auth headers