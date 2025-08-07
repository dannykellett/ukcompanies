# UK Companies SDK

A modern Python SDK for accessing the UK Companies House API.

## Features

- **Async-first**: Built with modern async/await patterns for optimal performance
- **Type-safe**: Full type hints and Pydantic models for data validation  
- **Developer-friendly**: Intuitive API with comprehensive documentation
- **Lightweight**: Minimal dependencies, fast installation
- **Well-tested**: Extensive test coverage with unit and integration tests

## Installation

```bash
pip install ukcompanies
```

## Quick Start

```python
import asyncio
from ukcompanies import CompaniesHouseClient

async def main():
    # Initialize the client with your API key
    client = CompaniesHouseClient(api_key="your-api-key")
    
    # Search for companies
    results = await client.search_companies("OpenAI")
    
    for company in results:
        print(f"{company.company_name} - {company.company_number}")
    
    # Get detailed company information
    company = await client.get_company("12345678")
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