"""Unit tests for filing models."""

from datetime import date

import pytest
from pydantic import ValidationError

from ukcompanies.models.filing import (
    FilingCategory,
    FilingHistoryItem,
    FilingHistoryList,
    FilingLinks,
    FilingTransaction,
    FilingType,
)


class TestFilingCategory:
    """Test FilingCategory enum."""

    def test_filing_category_values(self):
        """Test that filing categories have correct values."""
        assert FilingCategory.ACCOUNTS.value == "accounts"
        assert FilingCategory.ANNUAL_RETURN.value == "annual-return"
        assert FilingCategory.CAPITAL.value == "capital"
        assert FilingCategory.INCORPORATION.value == "incorporation"
        assert FilingCategory.CONFIRMATION_STATEMENT.value == "confirmation-statement"

    def test_filing_category_from_string(self):
        """Test creating category from string."""
        category = FilingCategory("accounts")
        assert category == FilingCategory.ACCOUNTS


class TestFilingType:
    """Test FilingType enum."""

    def test_filing_type_values(self):
        """Test that filing types have correct values."""
        assert FilingType.AA.value == "AA"
        assert FilingType.AR01.value == "AR01"
        assert FilingType.IN01.value == "IN01"
        assert FilingType.CS01.value == "CS01"

    def test_filing_type_from_string(self):
        """Test creating type from string."""
        filing_type = FilingType("AA")
        assert filing_type == FilingType.AA


class TestFilingLinks:
    """Test FilingLinks model."""

    def test_filing_links_minimal(self):
        """Test creating filing links with minimal data."""
        links = FilingLinks(self="/company/12345678/filing-history/ABC123")
        assert links.self == "/company/12345678/filing-history/ABC123"
        assert links.document_metadata is None

    def test_filing_links_with_document(self):
        """Test creating filing links with document metadata."""
        links = FilingLinks(
            self="/company/12345678/filing-history/ABC123",
            document_metadata="/document/doc123"
        )
        assert links.self == "/company/12345678/filing-history/ABC123"
        assert links.document_metadata == "/document/doc123"

    def test_filing_links_missing_self(self):
        """Test that self link is required."""
        with pytest.raises(ValidationError) as exc_info:
            FilingLinks()

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == ("self",)
        assert errors[0]["type"] == "missing"


class TestFilingTransaction:
    """Test FilingTransaction model."""

    def test_filing_transaction_minimal(self):
        """Test creating transaction with minimal required fields."""
        transaction = FilingTransaction(
            transaction_id="ABC123",
            category=FilingCategory.ACCOUNTS,
            date=date(2024, 1, 15),
            description="Annual accounts made up to 31 December 2023"
        )
        assert transaction.transaction_id == "ABC123"
        assert transaction.category == "accounts"
        assert transaction.filing_date == date(2024, 1, 15)
        assert transaction.description == "Annual accounts made up to 31 December 2023"
        assert transaction.type is None
        assert transaction.barcode is None
        assert transaction.pages is None

    def test_filing_transaction_complete(self):
        """Test creating transaction with all fields."""
        transaction = FilingTransaction(
            transaction_id="ABC123",
            category=FilingCategory.ACCOUNTS,
            date=date(2024, 1, 15),
            description="Annual accounts made up to 31 December 2023",
            type="AA",
            subcategory="small",
            barcode="X1234567",
            pages=25,
            links=FilingLinks(
                self="/company/12345678/filing-history/ABC123",
                document_metadata="/document/doc123"
            ),
            paper_filed=False,
            action_date=date(2024, 1, 14),
            description_values={"made_up_date": "2023-12-31"},
            annotations=[{"category": "accounts", "description": "ACCOUNTS-TYPE-SMALL"}]
        )
        assert transaction.transaction_id == "ABC123"
        assert transaction.category == "accounts"
        assert transaction.filing_date == date(2024, 1, 15)
        assert transaction.type == "AA"
        assert transaction.subcategory == "small"
        assert transaction.barcode == "X1234567"
        assert transaction.pages == 25
        assert transaction.links.self == "/company/12345678/filing-history/ABC123"
        assert transaction.paper_filed is False
        assert transaction.action_date == date(2024, 1, 14)
        assert transaction.description_values["made_up_date"] == "2023-12-31"
        assert len(transaction.annotations) == 1

    def test_filing_transaction_date_alias(self):
        """Test that 'date' field is aliased to 'filing_date'."""
        data = {
            "transaction_id": "ABC123",
            "category": "accounts",
            "date": "2024-01-15",
            "description": "Annual accounts"
        }
        transaction = FilingTransaction(**data)
        assert transaction.filing_date == date(2024, 1, 15)

    def test_filing_transaction_invalid_category(self):
        """Test that invalid category raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            FilingTransaction(
                transaction_id="ABC123",
                category="invalid-category",
                date=date(2024, 1, 15),
                description="Test"
            )

        errors = exc_info.value.errors()
        assert any("category" in str(error) for error in errors)


class TestFilingHistoryList:
    """Test FilingHistoryList model."""

    def test_filing_history_list_empty(self):
        """Test creating empty filing history list."""
        history = FilingHistoryList()
        assert history.items == []
        assert history.total_count == 0
        assert history.items_per_page == 25
        assert history.start_index == 0
        assert history.filing_history_status is None

    def test_filing_history_list_with_items(self):
        """Test creating filing history with items."""
        transaction1 = FilingTransaction(
            transaction_id="ABC123",
            category=FilingCategory.ACCOUNTS,
            date=date(2024, 1, 15),
            description="Annual accounts"
        )
        transaction2 = FilingTransaction(
            transaction_id="DEF456",
            category=FilingCategory.CONFIRMATION_STATEMENT,
            date=date(2024, 2, 1),
            description="Confirmation statement"
        )

        history = FilingHistoryList(
            items=[transaction1, transaction2],
            total_count=50,
            items_per_page=10,
            start_index=20,
            filing_history_status="filing-history-available"
        )

        assert len(history.items) == 2
        assert history.items[0].transaction_id == "ABC123"
        assert history.items[1].transaction_id == "DEF456"
        assert history.total_count == 50
        assert history.items_per_page == 10
        assert history.start_index == 20
        assert history.filing_history_status == "filing-history-available"


class TestFilingHistoryItem:
    """Test FilingHistoryItem model."""

    def test_filing_history_item_minimal(self):
        """Test creating history item with minimal fields."""
        item = FilingHistoryItem(
            transaction_id="ABC123",
            category=FilingCategory.ACCOUNTS,
            date=date(2024, 1, 15),
            description="Annual accounts"
        )
        assert item.transaction_id == "ABC123"
        assert item.category == "accounts"
        assert item.filing_date == date(2024, 1, 15)
        assert item.description == "Annual accounts"
        assert item.type is None
        assert item.barcode is None
        assert item.links is None

    def test_filing_history_item_with_optional_fields(self):
        """Test creating history item with optional fields."""
        item = FilingHistoryItem(
            transaction_id="ABC123",
            category=FilingCategory.ACCOUNTS,
            date=date(2024, 1, 15),
            description="Annual accounts",
            type="AA",
            barcode="X1234567",
            links=FilingLinks(
                self="/company/12345678/filing-history/ABC123",
                document_metadata="/document/doc123"
            )
        )
        assert item.transaction_id == "ABC123"
        assert item.type == "AA"
        assert item.barcode == "X1234567"
        assert item.links.self == "/company/12345678/filing-history/ABC123"
        assert item.links.document_metadata == "/document/doc123"

    def test_filing_history_item_date_alias(self):
        """Test that 'date' field is aliased to 'filing_date'."""
        data = {
            "transaction_id": "ABC123",
            "category": "accounts",
            "date": "2024-01-15",
            "description": "Annual accounts"
        }
        item = FilingHistoryItem(**data)
        assert item.filing_date == date(2024, 1, 15)
