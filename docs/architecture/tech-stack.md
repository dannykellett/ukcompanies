# Tech Stack

This is the **DEFINITIVE** technology selection for the project. These choices will guide all implementation decisions.

## Cloud Infrastructure
- **Provider:** N/A (SDK runs client-side)
- **Key Services:** N/A 
- **Deployment Regions:** PyPI (global distribution)

## Technology Stack Table

| Category | Technology | Version | Purpose | Rationale |
|----------|------------|---------|---------|-----------|
| **Language** | Python | 3.10+ | Primary development language | Modern Python features, type hints, async support |
| **Package Manager** | uv | 0.5.0+ | Dependency management & packaging | Fast, modern replacement for pip/poetry, PRD requirement |
| **HTTP Client** | httpx | 0.27.0 | Async HTTP operations | Best async HTTP client, connection pooling, HTTP/2 |
| **Data Validation** | pydantic | 2.9.0 | Response models & validation | Type safety, automatic validation, PRD requirement |
| **Testing Framework** | pytest | 8.3.0 | Unit & integration testing | Industry standard, great async support |
| **HTTP Mocking** | respx | 0.21.0 | Mock HTTP responses in tests | Works perfectly with httpx, PRD requirement |
| **Linting** | ruff | 0.7.0 | Code quality & formatting | Fast, comprehensive, replaces multiple tools |
| **Type Checking** | mypy | 1.11.0 | Static type checking | Ensures type safety across codebase |
| **Documentation** | mkdocs | 1.6.0 | API documentation | Clean docs with autodoc support |
| **Doc Theme** | mkdocs-material | 9.5.0 | Documentation theme | Professional, searchable docs |
| **Env Management** | python-dotenv | 1.0.1 | Environment variable loading | Zero-config experience for API keys |
| **CLI Framework** | click | 8.1.7 | Command-line interface | Powerful, user-friendly CLI creation |
| **Logging** | structlog | 24.4.0 | Structured logging | Better debugging, especially for async |
| **Date Handling** | python-dateutil | 2.9.0 | Parse API date responses | Robust date parsing from strings |