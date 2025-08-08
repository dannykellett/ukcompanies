# Examples

## Basic Examples

### Search and Display Companies

```python
import asyncio
from ukcompanies import AsyncClient

async def search_companies_example():
    async with AsyncClient() as client:
        # Search for technology companies
        results = await client.search_companies("technology")
        
        print(f"Found {results.total_results} companies (showing {len(results.items)}):")
        for company in results.items[:5]:  # Display first 5
            print(f"- {company.title} ({company.company_number})")
            print(f"  Status: {company.company_status}")
            print(f"  Address: {company.address_snippet}")
            print()

asyncio.run(search_companies_example())
```

### Get Company with Error Handling

```python
import asyncio
from ukcompanies import CompaniesHouseClient
from ukcompanies.exceptions import NotFoundError, CompaniesHouseAPIError

async def get_company_safe():
    client = CompaniesHouseClient()
    
    company_numbers = ["12345678", "87654321", "11111111"]
    
    for number in company_numbers:
        try:
            company = await client.get_company(number)
            print(f"✓ {company.company_name}")
        except NotFoundError:
            print(f"✗ Company {number} not found")
        except CompaniesHouseAPIError as e:
            print(f"✗ Error fetching {number}: {e}")

asyncio.run(get_company_safe())
```

## Advanced Examples

### Batch Company Lookup

```python
import asyncio
from typing import List
from ukcompanies import CompaniesHouseClient, CompanyProfile

async def batch_lookup(company_numbers: List[str]) -> List[CompanyProfile]:
    client = CompaniesHouseClient()
    
    # Create tasks for concurrent requests
    tasks = [client.get_company(number) for number in company_numbers]
    
    # Gather results (with error handling)
    results = []
    for task in asyncio.as_completed(tasks):
        try:
            company = await task
            results.append(company)
        except Exception as e:
            print(f"Failed to fetch company: {e}")
    
    return results

async def main():
    numbers = ["12345678", "87654321", "11223344"]
    companies = await batch_lookup(numbers)
    
    for company in companies:
        print(f"{company.company_name}: {company.company_status}")

asyncio.run(main())
```

### Export Search Results to CSV

```python
import asyncio
import csv
from ukcompanies import CompaniesHouseClient

async def export_search_to_csv(query: str, filename: str):
    client = CompaniesHouseClient()
    
    # Search for companies
    results = await client.search_companies(query, items_per_page=100)
    
    # Write to CSV
    with open(filename, 'w', newline='') as csvfile:
        fieldnames = [
            'company_number', 
            'company_name', 
            'company_status',
            'company_type',
            'date_of_creation',
            'address'
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for company in results:
            writer.writerow({
                'company_number': company.company_number,
                'company_name': company.company_name,
                'company_status': company.company_status,
                'company_type': company.company_type,
                'date_of_creation': company.date_of_creation,
                'address': f"{company.registered_office_address.address_line_1}, "
                          f"{company.registered_office_address.postal_code}"
            })
    
    print(f"Exported {len(results)} companies to {filename}")

asyncio.run(export_search_to_csv("fintech", "fintech_companies.csv"))
```

### CLI Tool Example

```python
import asyncio
import click
from ukcompanies import CompaniesHouseClient

@click.command()
@click.argument('query')
@click.option('--limit', default=10, help='Number of results to display')
@click.option('--export', help='Export results to CSV file')
def search_cli(query: str, limit: int, export: str):
    """Search for UK companies."""
    asyncio.run(_search(query, limit, export))

async def _search(query: str, limit: int, export: str):
    client = CompaniesHouseClient()
    
    results = await client.search_companies(query, items_per_page=limit)
    
    if export:
        # Export logic here
        print(f"Exported to {export}")
    else:
        for i, company in enumerate(results, 1):
            print(f"{i}. {company.company_name} ({company.company_number})")

if __name__ == '__main__':
    search_cli()
```

## Integration Examples

### Using with FastAPI

```python
from fastapi import FastAPI, HTTPException
from ukcompanies import CompaniesHouseClient
from ukcompanies.exceptions import NotFoundError

app = FastAPI()
client = CompaniesHouseClient()

@app.get("/company/{company_number}")
async def get_company(company_number: str):
    try:
        company = await client.get_company(company_number)
        return {
            "name": company.company_name,
            "status": company.company_status,
            "incorporated": company.date_of_creation,
        }
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Company not found")

@app.get("/search")
async def search_companies(q: str, limit: int = 10):
    results = await client.search_companies(q, items_per_page=limit)
    return [
        {
            "number": c.company_number,
            "name": c.company_name,
            "status": c.company_status,
        }
        for c in results
    ]
```

### Using with Django

```python
# views.py
from django.http import JsonResponse
from django.views import View
from asgiref.sync import async_to_sync
from ukcompanies import CompaniesHouseClient

client = CompaniesHouseClient()

class CompanySearchView(View):
    def get(self, request):
        query = request.GET.get('q', '')
        if not query:
            return JsonResponse({'error': 'Query parameter required'}, status=400)
        
        # Convert async to sync for Django
        results = async_to_sync(client.search_companies)(query)
        
        return JsonResponse({
            'results': [
                {
                    'number': c.company_number,
                    'name': c.company_name,
                    'status': c.company_status,
                }
                for c in results
            ]
        })
```