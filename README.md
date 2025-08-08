# UK Companies SDK

A modern Python SDK for accessing the UK Companies House API.

## Features

- **Async-first**: Built with modern async/await patterns for optimal performance
- **Type-safe**: Full type hints and Pydantic models for data validation  
- **Developer-friendly**: Intuitive API with comprehensive documentation
- **Lightweight**: Minimal dependencies, fast installation
- **Well-tested**: Extensive test coverage with unit and integration tests
- **Automatic Retry**: Smart retry logic with exponential backoff for rate-limited requests
- **Rate Limit Aware**: Intelligent handling of API rate limits with configurable retry strategies
- **Production Ready**: Published on PyPI, thoroughly tested with live API

## Installation

```bash
# Install from PyPI
pip install ukcompanies

# Or with uv
uv add ukcompanies
```

## Quick Start

```python
import asyncio
from ukcompanies import AsyncClient

async def main():
    # Initialize the client with your API key
    async with AsyncClient(api_key="your-api-key") as client:
        # Search for companies
        results = await client.search_companies("OpenAI")
        
        for company in results.items:
            print(f"{company.title} - {company.company_number}")
        
        # Get detailed company information
        company = await client.profile("12345678")
        print(f"Company: {company.company_name}")
        print(f"Status: {company.company_status}")

asyncio.run(main())
```

## Configuration

### API Key

You'll need an API key from Companies House. Get one by:

1. Registering at [Companies House Developer Hub](https://developer.company-information.service.gov.uk/)
2. Creating an application
3. Getting your API key

### Environment Variables

Create a `.env` file in your project root:

```bash
COMPANIES_HOUSE_API_KEY=your-api-key-here
```

## Advanced Configuration

### Retry Settings

The SDK automatically handles rate limits with intelligent retry logic. You can customize retry behavior:

```python
from ukcompanies import AsyncClient

# Custom retry configuration
async with AsyncClient(
    api_key="your-api-key",
    auto_retry=True,        # Enable automatic retry (default: True)
    max_retries=5,          # Maximum retry attempts (default: 3)
    backoff="exponential",  # Backoff strategy: "exponential" or "fixed" (default: "exponential")
    base_delay=1.0,         # Base delay in seconds (default: 1.0)
    max_delay=60.0,         # Maximum delay between retries (default: 60.0)
    jitter_range=1.0,       # Random jitter range (default: 1.0)
    on_retry=my_callback    # Optional callback for retry events
) as client:
    # Use client here
    pass

# Custom retry callback
async def my_retry_callback(attempt, delay, response):
    print(f"Retry attempt {attempt} after {delay}s delay")

async with AsyncClient(
    api_key="your-api-key",
    on_retry=my_retry_callback
) as client:
    # Use client here
    pass
```

The SDK respects `X-Ratelimit-Reset` headers from the API for intelligent wait times and uses exponential backoff with jitter to prevent thundering herd problems.

## Development

### Setup

This project uses `uv` for dependency management:

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv pip install -e ".[dev]"
```

### Testing

```bash
# Run tests
pytest

# Run tests with coverage
pytest --cov=ukcompanies

# Run type checking
mypy src/ukcompanies

# Run linting
ruff check src/ tests/

# Format code
ruff format src/ tests/
```

### Documentation

Documentation is built with MkDocs:

```bash
# Install documentation dependencies
uv pip install -e ".[docs]"

# Serve documentation locally
mkdocs serve

# Build documentation
mkdocs build
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Links

- [Documentation](https://github.com/yourusername/ukcompanies)
- [PyPI Package](https://pypi.org/project/ukcompanies/)
- [Companies House API Documentation](https://developer.company-information.service.gov.uk/api/docs/)