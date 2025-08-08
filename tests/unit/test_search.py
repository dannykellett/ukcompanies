"""Unit tests for search models."""

from datetime import date

from ukcompanies.models.address import Address
from ukcompanies.models.search import (
    AllSearchResult,
    CompanySearchItem,
    CompanySearchResult,
    DisqualifiedOfficerSearchItem,
    OfficerSearchItem,
    OfficerSearchResult,
    SearchResult,
)


class TestCompanySearchItem:
    """Test CompanySearchItem model."""

    def test_create_minimal_company_item(self):
        """Test creating company search item with minimal fields."""
        item = CompanySearchItem(
            company_number="12345678",
            title="Test Company Ltd",
        )
        assert item.company_number == "12345678"
        assert item.title == "Test Company Ltd"
        assert item.kind == "searchresults#company"

    def test_create_full_company_item(self):
        """Test creating company search item with all fields."""
        address = Address(
            address_line_1="123 Test Street",
            locality="London",
            postal_code="SW1A 1AA",
        )

        item = CompanySearchItem(
            company_number="12345678",
            company_type="ltd",
            title="Test Company Ltd",
            company_status="active",
            date_of_creation=date(2020, 1, 1),
            address=address,
            address_snippet="123 Test Street, London, SW1A 1AA",
            description="Test Company Ltd - 12345678",
            description_identifier=["incorporated-on"],
            matches={"title": [0, 4]},
            links={"self": "/company/12345678"},
        )

        assert item.company_number == "12345678"
        assert item.company_type == "ltd"
        assert item.title == "Test Company Ltd"
        assert item.company_status == "active"
        assert item.date_of_creation == date(2020, 1, 1)
        assert item.address.address_line_1 == "123 Test Street"
        assert item.address_snippet == "123 Test Street, London, SW1A 1AA"
        assert item.description == "Test Company Ltd - 12345678"
        assert item.description_identifier == ["incorporated-on"]
        assert item.matches == {"title": [0, 4]}
        assert item.links == {"self": "/company/12345678"}


class TestOfficerSearchItem:
    """Test OfficerSearchItem model."""

    def test_create_minimal_officer_item(self):
        """Test creating officer search item with minimal fields."""
        item = OfficerSearchItem(
            title="John Smith",
        )
        assert item.title == "John Smith"
        assert item.kind == "searchresults#officer"

    def test_create_full_officer_item(self):
        """Test creating officer search item with all fields."""
        address = Address(
            address_line_1="123 Test Street",
            locality="London",
            postal_code="SW1A 1AA",
        )

        item = OfficerSearchItem(
            title="John Smith",
            description="Director",
            description_identifiers=["appointment-count", "born-on"],
            appointment_count=5,
            date_of_birth={"month": 1, "year": 1980},
            address=address,
            address_snippet="123 Test Street, London",
            matches={"title": [0, 4]},
            snippet="John Smith, Director",
            links={"self": "/officers/ABC123/appointments"},
        )

        assert item.title == "John Smith"
        assert item.description == "Director"
        assert item.description_identifiers == ["appointment-count", "born-on"]
        assert item.appointment_count == 5
        assert item.date_of_birth == {"month": 1, "year": 1980}
        assert item.address.address_line_1 == "123 Test Street"
        assert item.address_snippet == "123 Test Street, London"
        assert item.matches == {"title": [0, 4]}
        assert item.snippet == "John Smith, Director"
        assert item.links == {"self": "/officers/ABC123/appointments"}


class TestDisqualifiedOfficerSearchItem:
    """Test DisqualifiedOfficerSearchItem model."""

    def test_create_disqualified_officer_item(self):
        """Test creating disqualified officer search item."""
        item = DisqualifiedOfficerSearchItem(
            title="Jane Doe",
            description="Disqualified Director",
            date_of_birth={"month": 6, "year": 1975},
            address_snippet="456 Another Street, Manchester",
        )

        assert item.title == "Jane Doe"
        assert item.description == "Disqualified Director"
        assert item.date_of_birth == {"month": 6, "year": 1975}
        assert item.address_snippet == "456 Another Street, Manchester"
        assert item.kind == "searchresults#disqualified-officer"


class TestSearchResult:
    """Test SearchResult base model."""

    def test_create_search_result(self):
        """Test creating search result with basic fields."""
        result = SearchResult(
            items=[],
            items_per_page=20,
            kind="search#test",
            page_number=1,
            start_index=0,
            total_results=0,
        )

        assert result.items == []
        assert result.items_per_page == 20
        assert result.kind == "search#test"
        assert result.page_number == 1
        assert result.start_index == 0
        assert result.total_results == 0

    def test_has_more_pages_property(self):
        """Test has_more_pages property."""
        # No more pages
        result = SearchResult(
            kind="test",
            items_per_page=20,
            start_index=0,
            total_results=10,
        )
        assert result.has_more_pages is False

        # Has more pages
        result = SearchResult(
            kind="test",
            items_per_page=20,
            start_index=0,
            total_results=50,
        )
        assert result.has_more_pages is True

        # Exactly at boundary
        result = SearchResult(
            kind="test",
            items_per_page=20,
            start_index=20,
            total_results=40,
        )
        assert result.has_more_pages is False

    def test_next_start_index_property(self):
        """Test next_start_index property."""
        result = SearchResult(
            kind="test",
            items_per_page=20,
            start_index=0,
            total_results=50,
        )
        assert result.next_start_index == 20

        result = SearchResult(
            kind="test",
            items_per_page=10,
            start_index=30,
            total_results=100,
        )
        assert result.next_start_index == 40

    def test_total_pages_property(self):
        """Test total_pages property."""
        # Exact pages
        result = SearchResult(
            kind="test",
            items_per_page=20,
            start_index=0,
            total_results=100,
        )
        assert result.total_pages == 5

        # Partial last page
        result = SearchResult(
            kind="test",
            items_per_page=20,
            start_index=0,
            total_results=95,
        )
        assert result.total_pages == 5

        # Single page
        result = SearchResult(
            kind="test",
            items_per_page=20,
            start_index=0,
            total_results=10,
        )
        assert result.total_pages == 1

        # No results
        result = SearchResult(
            kind="test",
            items_per_page=20,
            start_index=0,
            total_results=0,
        )
        assert result.total_pages == 0

        # Edge case: items_per_page is 0
        result = SearchResult(
            kind="test",
            items_per_page=0,
            start_index=0,
            total_results=100,
        )
        assert result.total_pages == 0


class TestCompanySearchResult:
    """Test CompanySearchResult model."""

    def test_create_company_search_result(self):
        """Test creating company search result."""
        item1 = CompanySearchItem(
            company_number="12345678",
            title="Company One",
        )
        item2 = CompanySearchItem(
            company_number="87654321",
            title="Company Two",
        )

        result = CompanySearchResult(
            items=[item1, item2],
            items_per_page=20,
            start_index=0,
            total_results=2,
        )

        assert len(result.items) == 2
        assert result.items[0].company_number == "12345678"
        assert result.items[1].company_number == "87654321"
        assert result.kind == "search#companies"


class TestOfficerSearchResult:
    """Test OfficerSearchResult model."""

    def test_create_officer_search_result(self):
        """Test creating officer search result."""
        item1 = OfficerSearchItem(title="John Smith")
        item2 = OfficerSearchItem(title="Jane Doe")

        result = OfficerSearchResult(
            items=[item1, item2],
            items_per_page=20,
            start_index=0,
            total_results=2,
        )

        assert len(result.items) == 2
        assert result.items[0].title == "John Smith"
        assert result.items[1].title == "Jane Doe"
        assert result.kind == "search#officers"


class TestAllSearchResult:
    """Test AllSearchResult model."""

    def test_create_all_search_result(self):
        """Test creating combined search result."""
        company_item = CompanySearchItem(
            company_number="12345678",
            title="Test Company",
        )
        officer_item = OfficerSearchItem(
            title="John Smith",
        )
        disqualified_item = DisqualifiedOfficerSearchItem(
            title="Jane Doe",
        )

        result = AllSearchResult(
            items=[company_item, officer_item, disqualified_item],
            items_per_page=20,
            start_index=0,
            total_results=3,
        )

        assert len(result.items) == 3
        assert result.kind == "search#all"

    def test_get_companies_method(self):
        """Test get_companies method."""
        company1 = CompanySearchItem(company_number="12345678", title="Company One")
        company2 = CompanySearchItem(company_number="87654321", title="Company Two")
        officer = OfficerSearchItem(title="John Smith")

        result = AllSearchResult(
            items=[company1, officer, company2],
            items_per_page=20,
            start_index=0,
            total_results=3,
        )

        companies = result.get_companies()
        assert len(companies) == 2
        assert companies[0].company_number == "12345678"
        assert companies[1].company_number == "87654321"

    def test_get_officers_method(self):
        """Test get_officers method."""
        company = CompanySearchItem(company_number="12345678", title="Company")
        officer1 = OfficerSearchItem(title="John Smith")
        officer2 = OfficerSearchItem(title="Jane Doe")

        result = AllSearchResult(
            items=[company, officer1, officer2],
            items_per_page=20,
            start_index=0,
            total_results=3,
        )

        officers = result.get_officers()
        assert len(officers) == 2
        assert officers[0].title == "John Smith"
        assert officers[1].title == "Jane Doe"

    def test_get_disqualified_officers_method(self):
        """Test get_disqualified_officers method."""
        company = CompanySearchItem(company_number="12345678", title="Company")
        officer = OfficerSearchItem(title="John Smith")
        disqualified1 = DisqualifiedOfficerSearchItem(title="Bad Actor 1")
        disqualified2 = DisqualifiedOfficerSearchItem(title="Bad Actor 2")

        result = AllSearchResult(
            items=[company, disqualified1, officer, disqualified2],
            items_per_page=20,
            start_index=0,
            total_results=4,
        )

        disqualified = result.get_disqualified_officers()
        assert len(disqualified) == 2
        assert disqualified[0].title == "Bad Actor 1"
        assert disqualified[1].title == "Bad Actor 2"
