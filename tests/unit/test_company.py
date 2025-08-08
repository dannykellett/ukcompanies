"""Unit tests for company models and endpoints."""

from datetime import date

import pytest
from pydantic import ValidationError

from ukcompanies.models.address import Address
from ukcompanies.models.company import (
    AccountingReference,
    Accounts,
    Company,
    CompanyStatus,
    CompanyType,
    ConfirmationStatement,
    Jurisdiction,
)


class TestCompanyStatus:
    """Test CompanyStatus enum."""

    def test_company_status_values(self):
        """Test that company status enum has expected values."""
        assert CompanyStatus.ACTIVE.value == "active"
        assert CompanyStatus.DISSOLVED.value == "dissolved"
        assert CompanyStatus.LIQUIDATION.value == "liquidation"
        assert CompanyStatus.RECEIVERSHIP.value == "receivership"


class TestCompanyType:
    """Test CompanyType enum."""

    def test_company_type_values(self):
        """Test that company type enum has expected values."""
        assert CompanyType.LTD.value == "ltd"
        assert CompanyType.PLC.value == "plc"
        assert CompanyType.LIMITED_LIABILITY_PARTNERSHIP.value == "llp"


class TestJurisdiction:
    """Test Jurisdiction enum."""

    def test_jurisdiction_values(self):
        """Test that jurisdiction enum has expected values."""
        assert Jurisdiction.ENGLAND_WALES.value == "england-wales"
        assert Jurisdiction.SCOTLAND.value == "scotland"
        assert Jurisdiction.NORTHERN_IRELAND.value == "northern-ireland"


class TestAccountingReference:
    """Test AccountingReference model."""

    def test_create_accounting_reference(self):
        """Test creating accounting reference with valid data."""
        ref = AccountingReference(day=31, month=12)
        assert ref.day == 31
        assert ref.month == 12

    def test_optional_fields(self):
        """Test that fields are optional."""
        ref = AccountingReference()
        assert ref.day is None
        assert ref.month is None

    def test_day_validation(self):
        """Test day field validation."""
        # Valid days
        ref = AccountingReference(day=1, month=1)
        assert ref.day == 1

        ref = AccountingReference(day=31, month=12)
        assert ref.day == 31

        # Invalid days
        with pytest.raises(ValidationError) as exc_info:
            AccountingReference(day=0, month=1)
        assert "greater than or equal to 1" in str(exc_info.value).lower()

        with pytest.raises(ValidationError) as exc_info:
            AccountingReference(day=32, month=1)
        assert "less than or equal to 31" in str(exc_info.value).lower()

    def test_month_validation(self):
        """Test month field validation."""
        # Valid months
        ref = AccountingReference(day=15, month=1)
        assert ref.month == 1

        ref = AccountingReference(day=15, month=12)
        assert ref.month == 12

        # Invalid months
        with pytest.raises(ValidationError) as exc_info:
            AccountingReference(day=15, month=0)
        assert "greater than or equal to 1" in str(exc_info.value).lower()

        with pytest.raises(ValidationError) as exc_info:
            AccountingReference(day=15, month=13)
        assert "less than or equal to 12" in str(exc_info.value).lower()


class TestConfirmationStatement:
    """Test ConfirmationStatement model."""

    def test_create_confirmation_statement(self):
        """Test creating confirmation statement with valid data."""
        stmt = ConfirmationStatement(
            next_due=date(2025, 1, 31),
            overdue=False,
            next_made_up_to=date(2025, 1, 15),
            last_made_up_to=date(2024, 1, 15),
        )
        assert stmt.next_due == date(2025, 1, 31)
        assert stmt.overdue is False
        assert stmt.next_made_up_to == date(2025, 1, 15)
        assert stmt.last_made_up_to == date(2024, 1, 15)

    def test_default_values(self):
        """Test default values."""
        stmt = ConfirmationStatement()
        assert stmt.next_due is None
        assert stmt.overdue is False
        assert stmt.next_made_up_to is None
        assert stmt.last_made_up_to is None


class TestAccounts:
    """Test Accounts model."""

    def test_create_accounts(self):
        """Test creating accounts with valid data."""
        accounts = Accounts(
            accounting_reference_date=AccountingReference(day=31, month=12),
            next_due=date(2025, 9, 30),
            overdue=False,
        )
        assert accounts.accounting_reference_date.day == 31
        assert accounts.accounting_reference_date.month == 12
        assert accounts.next_due == date(2025, 9, 30)
        assert accounts.overdue is False

    def test_optional_fields(self):
        """Test that fields are optional."""
        accounts = Accounts()
        assert accounts.accounting_reference_date is None
        assert accounts.next_due is None
        assert accounts.last_accounts is None
        assert accounts.next_accounts is None
        assert accounts.overdue is False


class TestCompany:
    """Test Company model."""

    def test_create_minimal_company(self):
        """Test creating company with minimal required fields."""
        company = Company(
            company_number="12345678",
            company_name="Test Company Ltd",
        )
        assert company.company_number == "12345678"
        assert company.company_name == "Test Company Ltd"
        assert company.company_status is None
        assert company.date_of_creation is None

    def test_create_full_company(self):
        """Test creating company with all fields."""
        address = Address(
            address_line_1="123 Test Street",
            locality="London",
            postal_code="SW1A 1AA",
        )
        accounts = Accounts(
            accounting_reference_date=AccountingReference(day=31, month=12),
            next_due=date(2025, 9, 30),
        )
        confirmation = ConfirmationStatement(
            next_due=date(2025, 1, 31),
            overdue=False,
        )

        company = Company(
            company_number="12345678",
            company_name="Test Company Ltd",
            company_status="active",
            company_status_detail="Active",
            date_of_creation=date(2020, 1, 1),
            type="ltd",
            jurisdiction="england-wales",
            sic_codes=["62012", "62020"],
            registered_office_address=address,
            accounts=accounts,
            confirmation_statement=confirmation,
            has_been_liquidated=False,
            has_insolvency_history=False,
            can_file=True,
        )

        assert company.company_number == "12345678"
        assert company.company_name == "Test Company Ltd"
        assert company.company_status == "active"
        assert company.date_of_creation == date(2020, 1, 1)
        assert company.type == "ltd"
        assert company.jurisdiction == "england-wales"
        assert company.sic_codes == ["62012", "62020"]
        assert company.registered_office_address.address_line_1 == "123 Test Street"
        assert company.accounts.accounting_reference_date.day == 31
        assert company.confirmation_statement.next_due == date(2025, 1, 31)

    def test_company_number_validation(self):
        """Test company number validation and normalization."""
        # Valid 8-character number
        company = Company(company_number="12345678", company_name="Test")
        assert company.company_number == "12345678"

        # Valid with letters
        company = Company(company_number="AB123456", company_name="Test")
        assert company.company_number == "AB123456"

        # Lowercase converted to uppercase
        company = Company(company_number="ab123456", company_name="Test")
        assert company.company_number == "AB123456"

        # Spaces removed
        company = Company(company_number="12 34 56 78", company_name="Test")
        assert company.company_number == "12345678"

        # 7-digit number padded
        company = Company(company_number="1234567", company_name="Test")
        assert company.company_number == "01234567"

        # Invalid - too short
        with pytest.raises(ValidationError) as exc_info:
            Company(company_number="12345", company_name="Test")
        assert "must be 8 characters" in str(exc_info.value)

        # Invalid - too long
        with pytest.raises(ValidationError) as exc_info:
            Company(company_number="123456789", company_name="Test")
        assert "must be 8 characters" in str(exc_info.value)

    def test_is_active_property(self):
        """Test is_active property."""
        company = Company(
            company_number="12345678",
            company_name="Test",
            company_status="active",
        )
        assert company.is_active is True

        company.company_status = "dissolved"
        assert company.is_active is False

        company.company_status = None
        assert company.is_active is False

    def test_is_dissolved_property(self):
        """Test is_dissolved property."""
        company = Company(
            company_number="12345678",
            company_name="Test",
            company_status="dissolved",
        )
        assert company.is_dissolved is True

        company.company_status = "active"
        assert company.is_dissolved is False

        company.company_status = None
        assert company.is_dissolved is False

    def test_display_status_property(self):
        """Test display_status property."""
        company = Company(
            company_number="12345678",
            company_name="Test",
            company_status="active",
        )
        assert company.display_status == "Active"

        company.company_status = "voluntary-arrangement"
        assert company.display_status == "Voluntary Arrangement"

        company.company_status_detail = "In Administration"
        assert company.display_status == "In Administration"

        company.company_status = None
        company.company_status_detail = None
        assert company.display_status == "Unknown"
