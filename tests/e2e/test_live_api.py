"""End-to-end tests with live Companies House API calls."""

import asyncio
import os
from datetime import datetime

import pytest

from ukcompanies import AsyncClient


@pytest.mark.e2e
class TestLiveCompaniesHouseAPI:
    """Tests that make actual calls to the Companies House API."""
    
    @pytest.fixture
    def api_key(self):
        """Get API key from environment."""
        api_key = os.getenv("COMPANIES_HOUSE_API_KEY")
        if not api_key:
            pytest.skip("COMPANIES_HOUSE_API_KEY not set - skipping live API tests")
        return api_key
    
    @pytest.mark.asyncio
    async def test_get_company_profile(self, api_key):
        """Test retrieving a real company profile from Companies House."""
        # Using a well-known company as a reliable test case
        # Marks and Spencer Group PLC: 00214436
        test_company_number = "00214436"
        
        async with AsyncClient(api_key=api_key) as client:
            # Get company profile
            company = await client.get_company(test_company_number)
            
            # Verify we got data back
            assert company is not None
            
            # Check that it's a Company model object with expected attributes
            assert hasattr(company, "company_number")
            assert company.company_number == test_company_number
            assert hasattr(company, "company_status")
            assert hasattr(company, "date_of_creation")
            
            # Log some details for debugging
            print(f"\n✅ Successfully retrieved company: {company.company_name}")
            print(f"   Number: {company.company_number}")
            print(f"   Status: {company.company_status}")
            print(f"   Created: {company.date_of_creation}")
            print(f"   Type: {company.type}")
            if hasattr(company, "sic_codes") and company.sic_codes:
                print(f"   SIC Codes: {company.sic_codes}")
    
    @pytest.mark.asyncio
    async def test_search_companies(self, api_key):
        """Test searching for companies by name."""
        search_query = "Tesco"
        
        async with AsyncClient(api_key=api_key) as client:
            # Search for companies
            results = await client.search_companies(search_query, items_per_page=5)
            
            # Verify we got results
            assert results is not None
            assert hasattr(results, "items")
            assert len(results.items) > 0
            
            # Check first result structure
            first_result = results.items[0]
            assert hasattr(first_result, "company_number")
            assert hasattr(first_result, "title")
            assert hasattr(first_result, "company_status")
            
            # Log results for debugging
            print(f"\n✅ Found {len(results.items)} companies matching '{search_query}':")
            for company in results.items[:3]:  # Show first 3
                print(f"   - {company.title} ({company.company_number})")
                print(f"     Status: {company.company_status}")
    
    @pytest.mark.asyncio
    async def test_get_company_officers(self, api_key):
        """Test retrieving officers for a real company."""
        # Using Tesco PLC which we know exists
        test_company_number = "00445790"
        
        async with AsyncClient(api_key=api_key) as client:
            # Get company officers
            officers = await client.get_officers(test_company_number, items_per_page=5)
            
            # Verify we got data
            assert officers is not None
            assert hasattr(officers, "items")
            
            if officers.items and len(officers.items) > 0:
                # Check officer structure
                first_officer = officers.items[0]
                assert hasattr(first_officer, "name")
                assert hasattr(first_officer, "officer_role")
                assert hasattr(first_officer, "appointed_on")
                
                # Log officer details
                print(f"\n✅ Retrieved {len(officers.items)} officers for company {test_company_number}:")
                for officer in officers.items[:3]:  # Show first 3
                    print(f"   - {officer.name}")
                    print(f"     Role: {officer.officer_role}")
                    print(f"     Appointed: {officer.appointed_on}")
            else:
                print(f"\n⚠️  No officers found for company {test_company_number}")
    
    @pytest.mark.asyncio
    async def test_rate_limit_handling(self, api_key):
        """Test that rate limit information is properly extracted."""
        test_company_number = "00214436"  # Marks & Spencer
        
        async with AsyncClient(api_key=api_key) as client:
            # Make a request
            await client.get_company(test_company_number)
            
            # Check rate limit info was captured
            rate_limit = client.rate_limit_info
            
            if rate_limit:
                assert rate_limit.limit > 0
                assert rate_limit.remain >= 0
                assert rate_limit.remain <= rate_limit.limit
                assert isinstance(rate_limit.reset, datetime)
                
                print(f"\n✅ Rate limit info captured:")
                print(f"   Remaining: {rate_limit.remain}/{rate_limit.limit}")
                print(f"   Reset at: {rate_limit.reset}")
                print(f"   Percent remaining: {rate_limit.percent_remaining:.1f}%")
            else:
                print("\n⚠️  No rate limit headers returned by API")
    
    @pytest.mark.asyncio
    async def test_invalid_company_number(self, api_key):
        """Test handling of invalid company numbers."""
        invalid_number = "INVALID123"
        
        async with AsyncClient(api_key=api_key) as client:
            # This should raise a ValidationError
            from ukcompanies.exceptions import ValidationError
            
            with pytest.raises(ValidationError) as exc_info:
                client.validate_company_number(invalid_number)
            
            assert "Invalid company number format" in str(exc_info.value)
            print(f"\n✅ Correctly rejected invalid company number: {invalid_number}")
    
    @pytest.mark.asyncio
    async def test_company_not_found(self, api_key):
        """Test handling when a company doesn't exist."""
        # Using a valid format but non-existent company
        non_existent = "99999999"
        
        async with AsyncClient(api_key=api_key) as client:
            from ukcompanies.exceptions import NotFoundError
            
            with pytest.raises(NotFoundError):
                await client.get_company(non_existent)
            
            print(f"\n✅ Correctly handled non-existent company: {non_existent}")
    
    @pytest.mark.asyncio
    async def test_filing_history(self, api_key):
        """Test retrieving filing history for a company."""
        # Using Tesco PLC which should have regular filings
        test_company_number = "00445790"  # Tesco PLC
        
        async with AsyncClient(api_key=api_key) as client:
            # Get filing history
            filings = await client.filing_history(
                test_company_number, 
                items_per_page=5
            )
            
            # Verify we got data
            assert filings is not None
            assert hasattr(filings, "items")
            
            if filings.items:
                first_filing = filings.items[0]
                assert hasattr(first_filing, "transaction_id")
                assert hasattr(first_filing, "type")
                assert hasattr(first_filing, "filing_date")
                
                print(f"\n✅ Retrieved filing history for {test_company_number}:")
                for filing in filings.items[:3]:  # Show first 3
                    description = filing.description if hasattr(filing, "description") else filing.type
                    print(f"   - {description}")
                    print(f"     Date: {filing.filing_date}")
                    print(f"     Type: {filing.type}")
            else:
                print(f"\n⚠️  No filing history found for {test_company_number}")


def main():
    """Run e2e tests directly with asyncio."""
    import sys
    
    # Check for API key
    api_key = os.getenv("COMPANIES_HOUSE_API_KEY")
    if not api_key:
        print("❌ Error: COMPANIES_HOUSE_API_KEY environment variable not set")
        print("Please set your Companies House API key:")
        print("  export COMPANIES_HOUSE_API_KEY='your-api-key-here'")
        sys.exit(1)
    
    print("🚀 Starting live Companies House API tests...")
    print(f"   Using API key: {api_key[:8]}...")
    
    # Create test instance
    test_suite = TestLiveCompaniesHouseAPI()
    
    # Run each test
    async def run_tests():
        """Run all tests sequentially."""
        try:
            print("\n1️⃣  Testing company profile retrieval...")
            await test_suite.test_get_company_profile(api_key)
            
            print("\n2️⃣  Testing company search...")
            await test_suite.test_search_companies(api_key)
            
            print("\n3️⃣  Testing officer retrieval...")
            await test_suite.test_get_company_officers(api_key)
            
            print("\n4️⃣  Testing rate limit handling...")
            await test_suite.test_rate_limit_handling(api_key)
            
            print("\n5️⃣  Testing invalid company number validation...")
            await test_suite.test_invalid_company_number(api_key)
            
            print("\n6️⃣  Testing non-existent company handling...")
            await test_suite.test_company_not_found(api_key)
            
            print("\n7️⃣  Testing filing history retrieval...")
            await test_suite.test_filing_history(api_key)
            
            print("\n✅ All tests passed successfully!")
            return 0
            
        except Exception as e:
            print(f"\n❌ Test failed with error: {e}")
            import traceback
            traceback.print_exc()
            return 1
    
    # Run the async tests
    return asyncio.run(run_tests())


if __name__ == "__main__":
    exit(main())