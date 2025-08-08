# API Reference

## AsyncClient

The main async client class for interacting with the Companies House API.

### Initialization

```python
from ukcompanies import AsyncClient

# Use as context manager (recommended)
async with AsyncClient(
    api_key="your-api-key",  # Optional if set in environment
    base_url="https://api.company-information.service.gov.uk",  # Optional, uses default
    timeout=30.0,  # Optional, request timeout in seconds
    auto_retry=True,  # Optional, enable automatic retry (default: True)
    max_retries=3,  # Optional, maximum retry attempts (default: 3)
    backoff="exponential",  # Optional, backoff strategy (default: "exponential")
    base_delay=1.0,  # Optional, base delay in seconds (default: 1.0)
    max_delay=60.0,  # Optional, maximum delay between retries (default: 60.0)
    jitter_range=1.0,  # Optional, random jitter range (default: 1.0)
    on_retry=callback_func,  # Optional, callback for retry events
)
```

### Retry Configuration

The client supports automatic retry for rate-limited requests (HTTP 429) and network errors:

#### Parameters

- `auto_retry` (bool): Enable automatic retry on rate limits (default: True)
- `max_retries` (int): Maximum number of retry attempts (default: 3)
- `backoff` (str): Backoff strategy - "exponential" or "fixed" (default: "exponential")
- `base_delay` (float): Base delay in seconds for backoff calculation (default: 1.0)
- `max_delay` (float): Maximum delay in seconds between retries (default: 60.0)
- `jitter_range` (float): Maximum jitter to add to delay in seconds (default: 1.0)
- `on_retry` (callable): Optional callback function called before each retry

#### Retry Callback

```python
async def my_retry_callback(attempt: int, delay: float, response):
    print(f"Retrying request - attempt {attempt}, waiting {delay}s")

async with AsyncClient(
    api_key="your-api-key",
    on_retry=my_retry_callback
) as client:
    # Use client here
    pass
```

The SDK automatically respects `X-Ratelimit-Reset` headers from the API and uses intelligent wait times.

### Methods

#### search_companies

Search for companies by name or number.

```python
async def search_companies(
    query: str,
    items_per_page: int = 20,
    start_index: int = 0
) -> List[CompanySearchResult]
```

**Parameters:**
- `query` (str): The search query
- `items_per_page` (int): Number of results per page (default: 20, max: 100)
- `start_index` (int): Index of the first result (default: 0)

**Returns:**
- List of `CompanySearchResult` objects

#### get_company

Get detailed information about a specific company.

```python
async def get_company(company_number: str) -> CompanyProfile
```

**Parameters:**
- `company_number` (str): The company number

**Returns:**
- `CompanyProfile` object with full company details

## Models

### CompanySearchResult

Represents a company in search results.

**Attributes:**
- `company_number` (str): The company registration number
- `company_name` (str): The company name
- `company_status` (str): Current status (e.g., "active", "dissolved")
- `company_type` (str): Type of company
- `date_of_creation` (date): Date of incorporation
- `registered_office_address` (Address): Registered office location

### CompanyProfile

Detailed company information.

**Attributes:**
- All attributes from `CompanySearchResult`
- `sic_codes` (List[str]): Standard Industrial Classification codes
- `previous_company_names` (List[PreviousName]): Historical names
- `accounts` (Accounts): Accounting reference dates
- `confirmation_statement` (ConfirmationStatement): Annual confirmation details

### Address

Company address information.

**Attributes:**
- `address_line_1` (str): First line of address
- `address_line_2` (str, optional): Second line of address
- `locality` (str): City or town
- `postal_code` (str): Postal/ZIP code
- `country` (str): Country

## Error Handling

The SDK raises specific exceptions for different error scenarios:

```python
from ukcompanies.exceptions import (
    CompaniesHouseAPIError,
    RateLimitError,
    AuthenticationError,
    NotFoundError,
)

try:
    company = await client.get_company("12345678")
except NotFoundError:
    print("Company not found")
except RateLimitError:
    print("Rate limit exceeded, please wait")
except AuthenticationError:
    print("Invalid API key")
except CompaniesHouseAPIError as e:
    print(f"API error: {e}")
```