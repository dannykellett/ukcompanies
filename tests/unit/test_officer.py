"""Unit tests for officer models."""

from datetime import date

import pytest
from pydantic import ValidationError

from ukcompanies.models.officer import (
    IdentificationType,
    Officer,
    OfficerList,
    OfficerRole,
    PartialDate,
)


class TestPartialDate:
    """Test PartialDate model."""

    def test_valid_partial_date(self):
        """Test creating a valid partial date."""
        pd = PartialDate(month=6, year=1980)
        assert pd.month == 6
        assert pd.year == 1980
        assert str(pd) == "06/1980"

    def test_as_tuple(self):
        """Test getting partial date as tuple."""
        pd = PartialDate(month=12, year=2000)
        assert pd.as_tuple == (2000, 12)

    def test_invalid_month_low(self):
        """Test validation of month below range."""
        with pytest.raises(ValidationError) as exc_info:
            PartialDate(month=0, year=1980)
        assert "greater than or equal to 1" in str(exc_info.value)

    def test_invalid_month_high(self):
        """Test validation of month above range."""
        with pytest.raises(ValidationError) as exc_info:
            PartialDate(month=13, year=1980)
        assert "less than or equal to 12" in str(exc_info.value)

    def test_invalid_year_low(self):
        """Test validation of year below range."""
        with pytest.raises(ValidationError) as exc_info:
            PartialDate(month=6, year=1799)
        assert "greater than or equal to 1800" in str(exc_info.value)

    def test_invalid_year_high(self):
        """Test validation of year above range."""
        with pytest.raises(ValidationError) as exc_info:
            PartialDate(month=6, year=2101)
        assert "less than or equal to 2100" in str(exc_info.value)

    def test_string_formatting(self):
        """Test string formatting with leading zeros."""
        pd = PartialDate(month=1, year=2020)
        assert str(pd) == "01/2020"


class TestOfficer:
    """Test Officer model."""

    @pytest.fixture
    def basic_officer_data(self):
        """Basic officer data for tests."""
        return {
            "name": "John Smith",
            "officer_id": "abc123",
            "officer_role": "director",
            "appointed_on": "2020-01-01",
        }

    def test_create_basic_officer(self, basic_officer_data):
        """Test creating a basic officer."""
        officer = Officer(**basic_officer_data)
        assert officer.name == "John Smith"
        assert officer.officer_id == "abc123"
        assert officer.officer_role == OfficerRole.DIRECTOR
        assert officer.appointed_on == date(2020, 1, 1)

    def test_officer_with_date_of_birth(self, basic_officer_data):
        """Test officer with privacy-compliant date of birth."""
        basic_officer_data["date_of_birth"] = {"month": 3, "year": 1970}
        officer = Officer(**basic_officer_data)
        assert officer.date_of_birth.month == 3
        assert officer.date_of_birth.year == 1970

    def test_is_active_not_resigned(self, basic_officer_data):
        """Test is_active property when not resigned."""
        officer = Officer(**basic_officer_data)
        assert officer.is_active is True

    def test_is_active_resigned(self, basic_officer_data):
        """Test is_active property when resigned."""
        basic_officer_data["resigned_on"] = "2021-12-31"
        officer = Officer(**basic_officer_data)
        assert officer.is_active is False

    def test_is_corporate_regular(self, basic_officer_data):
        """Test is_corporate property for regular officer."""
        officer = Officer(**basic_officer_data)
        assert officer.is_corporate is False

    def test_is_corporate_true(self, basic_officer_data):
        """Test is_corporate property for corporate officer."""
        basic_officer_data["officer_role"] = "corporate-director"
        officer = Officer(**basic_officer_data)
        assert officer.is_corporate is True

    def test_validate_empty_officer_id(self, basic_officer_data):
        """Test validation of empty officer ID."""
        basic_officer_data["officer_id"] = "   "
        officer = Officer(**basic_officer_data)
        assert officer.officer_id is None

    def test_officer_with_address(self, basic_officer_data):
        """Test officer with address."""
        basic_officer_data["address"] = {
            "address_line_1": "123 Main St",
            "locality": "London",
            "postal_code": "SW1A 1AA",
        }
        officer = Officer(**basic_officer_data)
        assert officer.address.address_line_1 == "123 Main St"
        assert officer.address.locality == "London"

    def test_officer_with_all_fields(self, basic_officer_data):
        """Test officer with all optional fields."""
        basic_officer_data.update({
            "date_of_birth": {"month": 5, "year": 1965},
            "nationality": "British",
            "country_of_residence": "United Kingdom",
            "occupation": "Company Director",
            "identification": {
                "identification_type": "uk-limited-company",
                "registration_number": "12345678",
            },
            "address": {
                "address_line_1": "456 High Street",
                "locality": "Manchester",
                "postal_code": "M1 1AA",
            },
            "links": {
                "self": "/officers/abc123",
                "appointments": "/officers/abc123/appointments",
            },
        })
        officer = Officer(**basic_officer_data)
        assert officer.nationality == "British"
        assert officer.country_of_residence == "United Kingdom"
        assert officer.occupation == "Company Director"
        assert officer.identification["registration_number"] == "12345678"


class TestOfficerList:
    """Test OfficerList model."""

    @pytest.fixture
    def officer_list_data(self):
        """Officer list data for tests."""
        return {
            "items": [
                {
                    "name": "John Smith",
                    "officer_role": "director",
                    "appointed_on": "2020-01-01",
                },
                {
                    "name": "Jane Doe",
                    "officer_role": "secretary",
                    "appointed_on": "2020-02-01",
                    "resigned_on": "2021-01-01",
                },
            ],
            "active_count": 1,
            "inactive_count": 0,
            "resigned_count": 1,
            "items_per_page": 35,
            "start_index": 0,
            "total_results": 2,
        }

    def test_create_officer_list(self, officer_list_data):
        """Test creating an officer list."""
        officer_list = OfficerList(**officer_list_data)
        assert len(officer_list.items) == 2
        assert officer_list.active_count == 1
        assert officer_list.resigned_count == 1

    def test_has_more_pages_false(self, officer_list_data):
        """Test has_more_pages when no more pages."""
        officer_list = OfficerList(**officer_list_data)
        assert officer_list.has_more_pages is False

    def test_has_more_pages_true(self, officer_list_data):
        """Test has_more_pages when more pages exist."""
        officer_list_data["total_results"] = 50
        officer_list = OfficerList(**officer_list_data)
        assert officer_list.has_more_pages is True

    def test_next_start_index(self, officer_list_data):
        """Test calculating next start index."""
        officer_list = OfficerList(**officer_list_data)
        assert officer_list.next_start_index == 35

    def test_empty_officer_list(self):
        """Test creating an empty officer list."""
        officer_list = OfficerList()
        assert officer_list.items == []
        assert officer_list.has_more_pages is False

    def test_officer_list_with_links(self, officer_list_data):
        """Test officer list with pagination links."""
        officer_list_data["links"] = {
            "self": "/company/12345678/officers",
            "next": "/company/12345678/officers?start_index=35",
        }
        officer_list = OfficerList(**officer_list_data)
        assert officer_list.links["self"] == "/company/12345678/officers"


class TestOfficerRole:
    """Test OfficerRole enum."""

    def test_director_role(self):
        """Test director role."""
        assert OfficerRole.DIRECTOR == "director"

    def test_secretary_role(self):
        """Test secretary role."""
        assert OfficerRole.SECRETARY == "secretary"

    def test_llp_member_role(self):
        """Test LLP member role."""
        assert OfficerRole.LLP_MEMBER == "llp-member"

    def test_corporate_director_role(self):
        """Test corporate director role."""
        assert OfficerRole.CORPORATE_DIRECTOR == "corporate-director"


class TestIdentificationType:
    """Test IdentificationType enum."""

    def test_uk_limited_company(self):
        """Test UK limited company type."""
        assert IdentificationType.UK_LIMITED_COMPANY == "uk-limited-company"

    def test_eea_company(self):
        """Test EEA company type."""
        assert IdentificationType.EEA_COMPANY == "eea-company"

    def test_non_eea_company(self):
        """Test non-EEA company type."""
        assert IdentificationType.NON_EEA_COMPANY == "non-eea-company"

    def test_other_type(self):
        """Test other identification type."""
        assert IdentificationType.OTHER == "other"
