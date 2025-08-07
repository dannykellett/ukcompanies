# Source Tree

```plaintext
ukcompanies/
├── src/
│   └── ukcompanies/
│       ├── __init__.py              # Package initialization, version export
│       ├── client.py                # AsyncClient main class
│       ├── auth.py                  # Authentication handler
│       ├── retry.py                 # Retry logic and backoff strategies
│       ├── exceptions.py            # Custom exception classes
│       ├── config.py                # Configuration and constants
│       │
│       ├── models/                  # Pydantic models
│       │   ├── __init__.py
│       │   ├── base.py             # Base models with common fields
│       │   ├── company.py          # Company-related models
│       │   ├── officer.py          # Officer-related models
│       │   ├── search.py           # Search result models
│       │   ├── filing.py           # Filing history models
│       │   ├── address.py          # Address models
│       │   ├── psc.py              # Persons with significant control
│       │   └── rate_limit.py       # Rate limiting models
│       │
│       ├── services/                # Service modules for API endpoints
│       │   ├── __init__.py
│       │   ├── base.py             # Base service class
│       │   ├── search.py           # Search operations
│       │   ├── company.py          # Company operations
│       │   ├── officer.py          # Officer operations
│       │   └── document.py         # Document operations
│       │
│       └── cli/                     # CLI module
│           ├── __init__.py
│           ├── main.py             # CLI entry point
│           └── formatters.py       # Output formatting
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py                 # Pytest fixtures and configuration
│   ├── fixtures/                    # Test data fixtures
│   │   ├── __init__.py
│   │   ├── companies.json          # Sample company responses
│   │   ├── officers.json           # Sample officer responses
│   │   └── errors.json             # Error response samples
│   │
│   ├── unit/                       # Unit tests
│   │   ├── __init__.py
│   │   ├── test_client.py         # Client tests
│   │   ├── test_auth.py           # Authentication tests
│   │   ├── test_retry.py          # Retry logic tests
│   │   ├── test_models.py         # Model validation tests
│   │   └── test_exceptions.py     # Exception handling tests
│   │
│   ├── integration/                # Integration tests with mocked API
│   │   ├── __init__.py
│   │   ├── test_search.py         # Search endpoint tests
│   │   ├── test_company.py        # Company endpoint tests
│   │   ├── test_officer.py        # Officer endpoint tests
│   │   └── test_pagination.py    # Pagination tests
│   │
│   └── e2e/                        # End-to-end tests (optional, real API)
│       ├── __init__.py
│       └── test_real_api.py       # Tests against sandbox API
│
├── docs/                           # Documentation
│   ├── index.md                   # Documentation home
│   ├── quickstart.md              # Getting started guide
│   ├── api-reference.md           # API documentation
│   ├── examples.md                # Usage examples
│   └── architecture.md            # This architecture document
│
├── scripts/                        # Development scripts
│   ├── generate_types.py          # Generate types from API responses
│   └── test_coverage.sh           # Run tests with coverage
│
├── .env.example                    # Example environment variables
├── .gitignore                      # Git ignore rules
├── pyproject.toml                  # Project configuration (uv, ruff, pytest)
├── README.md                       # Project readme
├── LICENSE                         # MIT license
├── CHANGELOG.md                    # Version history
└── mkdocs.yml                      # Documentation configuration
```