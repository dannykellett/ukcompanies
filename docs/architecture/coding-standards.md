# Coding Standards

## Core Standards
- **Languages & Runtimes:** Python 3.10+ with modern syntax (union types, match statements, async/await)
- **Style & Linting:** ruff with default configuration in pyproject.toml (line length 100, Black formatting)
- **Test Organization:** Tests mirror source structure in tests/ directory, test files prefixed with `test_`

## Naming Conventions

| Element | Convention | Example |
|---------|------------|---------|
| Classes | PascalCase | `CompaniesHouseClient` |
| Functions/Methods | snake_case | `search_companies()` |
| Constants | UPPER_SNAKE | `MAX_RETRIES` |
| Private Methods | Leading underscore | `_calculate_backoff()` |
| Type Aliases | PascalCase | `CompanyDict = Dict[str, Any]` |

## Critical Rules
- **Never use print() or console output in library code:** Use structlog logger exclusively for all output
- **All public methods must have type hints:** Both parameters and return types required
- **All API responses must use Pydantic models:** Never return raw dicts from public methods
- **Never hardcode API keys or secrets:** Must use environment variables or constructor parameters
- **All async functions must be prefixed with async:** No sync wrappers in v1.0
- **Rate limit headers must always be checked:** Every API response must extract and log rate limit status
- **Use httpx.AsyncClient as context manager:** Always use `async with` to ensure proper cleanup
- **Validate company numbers before API calls:** Use regex `^[0-9A-Z]{8}$` or `^[0-9]{7,8}$` for older companies