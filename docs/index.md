# UK Companies SDK

Welcome to the UK Companies SDK documentation!

## Overview

The UK Companies SDK is a modern Python library for accessing the UK Companies House API. It provides a simple, type-safe, and async-first interface for searching and retrieving company information from the UK Companies House registry.

## Features

- 🚀 **Async-first**: Built with modern async/await patterns for optimal performance
- 🔒 **Type-safe**: Full type hints and Pydantic models for data validation
- 🛠️ **Developer-friendly**: Intuitive API with comprehensive documentation
- 📦 **Lightweight**: Minimal dependencies, fast installation
- 🧪 **Well-tested**: Extensive test coverage with unit and integration tests

## Installation

```bash
pip install ukcompanies
```

## Quick Example

```python
from ukcompanies import CompaniesHouseClient

# Initialize the client
client = CompaniesHouseClient(api_key="your-api-key")

# Search for companies
results = await client.search_companies("OpenAI")

# Get company details
company = await client.get_company("12345678")
```

## Next Steps

- [Quickstart Guide](quickstart.md) - Get up and running quickly
- [API Reference](api-reference.md) - Detailed API documentation
- [Examples](examples.md) - Common usage patterns and examples