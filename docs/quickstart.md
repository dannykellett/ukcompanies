# Quickstart Guide

This guide will help you get started with the UK Companies SDK.

## Installation

Install the package using pip:

```bash
pip install ukcompanies
```

## Configuration

### API Key

You'll need an API key from Companies House. You can obtain one by:

1. Registering at [Companies House Developer Hub](https://developer.company-information.service.gov.uk/)
2. Creating an application
3. Getting your API key

### Environment Variables

Create a `.env` file in your project root:

```bash
COMPANIES_HOUSE_API_KEY=your-api-key-here
```

## Basic Usage

### Initialize the Client

```python
from ukcompanies import AsyncClient
import asyncio

async def main():
    # Initialize with API key
    async with AsyncClient(api_key="your-api-key") as client:
        # Your code here
        pass
    
    # Or load from environment
    async with AsyncClient() as client:  # Reads COMPANIES_HOUSE_API_KEY env var
        # Your code here
        pass
    
asyncio.run(main())
```

### Search for Companies

```python
# Search by company name
results = await client.search_companies("Tesla")

for company in results.items:
    print(f"{company.title} - {company.company_number}")
```

### Get Company Details

```python
# Get detailed information about a specific company
company = await client.profile("00445790")  # Tesco PLC

print(f"Name: {company.company_name}")
print(f"Status: {company.company_status}")
print(f"Incorporated: {company.date_of_creation}")
```

## Next Steps

- Explore the [API Reference](api-reference.md) for all available methods
- Check out [Examples](examples.md) for more complex use cases