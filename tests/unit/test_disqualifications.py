"""Unit tests for disqualification models."""

from datetime import date

import pytest

from ukcompanies.models.disqualification import (
    Disqualification,
    DisqualificationItem,
    DisqualificationList,
    DisqualificationReason,
)


class TestDisqualification:
    """Test Disqualification model."""

    @pytest.fixture
    def basic_disqualification_data(self):
        """Basic disqualification data for tests."""
        return {
            "disqualified_from": "2020-01-01",
            "disqualified_until": "2025-01-01",
            "reason": {
                "description_identifier": "misconduct",
                "act": "company-directors-disqualification-act-1986",
                "section": "section-6",
                "description": "Misconduct in connection with company",
            },
        }

    def test_create_basic_disqualification(self, basic_disqualification_data):
        """Test creating a basic disqualification."""
        disq = Disqualification(**basic_disqualification_data)
        assert disq.disqualified_from == date(2020, 1, 1)
        assert disq.disqualified_until == date(2025, 1, 1)
        assert disq.reason["description_identifier"] == "misconduct"

    def test_is_active_current(self, basic_disqualification_data):
        """Test is_active property for current disqualification."""
        # Set dates to ensure it's active
        from datetime import date as dt
        from datetime import timedelta
        today = dt.today()
        basic_disqualification_data["disqualified_from"] = (today - timedelta(days=365)).isoformat()
        basic_disqualification_data["disqualified_until"] = (
            today + timedelta(days=365)
        ).isoformat()

        disq = Disqualification(**basic_disqualification_data)
        assert disq.is_active is True

    def test_is_active_expired(self, basic_disqualification_data):
        """Test is_active property for expired disqualification."""
        basic_disqualification_data["disqualified_from"] = "2010-01-01"
        basic_disqualification_data["disqualified_until"] = "2015-01-01"
        disq = Disqualification(**basic_disqualification_data)
        assert disq.is_active is False

    def test_has_expired(self, basic_disqualification_data):
        """Test has_expired property."""
        basic_disqualification_data["disqualified_until"] = "2015-01-01"
        disq = Disqualification(**basic_disqualification_data)
        assert disq.has_expired is True

    def test_reason_properties(self, basic_disqualification_data):
        """Test reason property accessors."""
        disq = Disqualification(**basic_disqualification_data)
        assert disq.reason_description == "Misconduct in connection with company"
        assert disq.reason_act == "company-directors-disqualification-act-1986"

    def test_duration_years(self, basic_disqualification_data):
        """Test calculating duration in years."""
        disq = Disqualification(**basic_disqualification_data)
        assert disq.duration_years == pytest.approx(5.0, rel=0.01)

    def test_court_order_disqualification(self, basic_disqualification_data):
        """Test disqualification with court order details."""
        basic_disqualification_data.update({
            "court_name": "High Court of Justice",
            "court_order_date": "2019-12-01",
            "case_identifier": "HC-2019-001234",
            "heard_on": "2019-11-15",
        })
        disq = Disqualification(**basic_disqualification_data)
        assert disq.court_name == "High Court of Justice"
        assert disq.court_order_date == date(2019, 12, 1)
        assert disq.case_identifier == "HC-2019-001234"

    def test_undertaking_disqualification(self, basic_disqualification_data):
        """Test disqualification by undertaking."""
        basic_disqualification_data.update({
            "undertaken_on": "2019-12-15",
            "is_undertaking": True,
        })
        disq = Disqualification(**basic_disqualification_data)
        assert disq.undertaken_on == date(2019, 12, 15)
        assert disq.is_undertaking is True

    def test_disqualification_with_companies(self, basic_disqualification_data):
        """Test disqualification with company names."""
        basic_disqualification_data["company_names"] = [
            "Failed Company Ltd",
            "Another Failed Company Ltd",
        ]
        disq = Disqualification(**basic_disqualification_data)
        assert len(disq.company_names) == 2
        assert "Failed Company Ltd" in disq.company_names

    def test_disqualification_with_address(self, basic_disqualification_data):
        """Test disqualification with address."""
        basic_disqualification_data["address"] = {
            "address_line_1": "123 Main St",
            "locality": "London",
            "postal_code": "SW1A 1AA",
        }
        disq = Disqualification(**basic_disqualification_data)
        assert disq.address.address_line_1 == "123 Main St"


class TestDisqualificationItem:
    """Test DisqualificationItem model."""

    @pytest.fixture
    def disqualification_item_data(self):
        """Disqualification item data for tests."""
        return {
            "forename": "John",
            "surname": "Smith",
            "title": "Mr",
            "date_of_birth": "1970",
            "disqualifications": [
                {
                    "disqualified_from": "2020-01-01",
                    "disqualified_until": "2025-01-01",
                    "reason": {
                        "description_identifier": "misconduct",
                        "description": "Misconduct",
                    },
                },
            ],
        }

    def test_create_disqualification_item(self, disqualification_item_data):
        """Test creating a disqualification item."""
        item = DisqualificationItem(**disqualification_item_data)
        assert item.forename == "John"
        assert item.surname == "Smith"
        assert len(item.disqualifications) == 1

    def test_full_name(self, disqualification_item_data):
        """Test getting full name."""
        item = DisqualificationItem(**disqualification_item_data)
        assert item.full_name == "Mr John Smith"

    def test_full_name_with_other_forenames(self, disqualification_item_data):
        """Test full name with other forenames."""
        disqualification_item_data["other_forenames"] = "Robert"
        item = DisqualificationItem(**disqualification_item_data)
        assert item.full_name == "Mr John Robert Smith"

    def test_full_name_corporate(self):
        """Test full name for corporate officer."""
        item = DisqualificationItem(
            company_name="Corporate Officer Ltd",
            company_number="12345678",
            disqualifications=[
                {
                    "disqualified_from": "2020-01-01",
                    "disqualified_until": "2025-01-01",
                }
            ],
        )
        assert item.full_name == "Corporate Officer Ltd"

    def test_active_disqualifications(self, disqualification_item_data):
        """Test getting active disqualifications."""
        from datetime import date as dt
        from datetime import timedelta
        today = dt.today()

        # Add one active and one expired disqualification
        disqualification_item_data["disqualifications"] = [
            {
                "disqualified_from": (today - timedelta(days=365)).isoformat(),
                "disqualified_until": (today + timedelta(days=365)).isoformat(),
            },
            {
                "disqualified_from": "2010-01-01",
                "disqualified_until": "2015-01-01",
            },
        ]
        item = DisqualificationItem(**disqualification_item_data)
        active = item.active_disqualifications
        assert len(active) == 1
        assert active[0].is_active is True

    def test_has_active_disqualifications(self, disqualification_item_data):
        """Test checking for active disqualifications."""
        from datetime import date as dt
        from datetime import timedelta
        today = dt.today()

        disqualification_item_data["disqualifications"][0]["disqualified_from"] = (
            today - timedelta(days=365)
        ).isoformat()
        disqualification_item_data["disqualifications"][0]["disqualified_until"] = (
            today + timedelta(days=365)
        ).isoformat()

        item = DisqualificationItem(**disqualification_item_data)
        assert item.has_active_disqualifications is True

    def test_permissions_to_act(self, disqualification_item_data):
        """Test permissions to act despite disqualification."""
        disqualification_item_data["permissions_to_act"] = [
            {
                "company_name": "Special Company Ltd",
                "company_number": "12345678",
                "granted_on": "2021-01-01",
                "expires_on": "2023-01-01",
            }
        ]
        item = DisqualificationItem(**disqualification_item_data)
        assert len(item.permissions_to_act) == 1
        assert item.permissions_to_act[0]["company_name"] == "Special Company Ltd"


class TestDisqualificationList:
    """Test DisqualificationList model."""

    @pytest.fixture
    def disqualification_list_data(self):
        """Disqualification list data for tests."""
        return {
            "items": [
                {
                    "forename": "John",
                    "surname": "Smith",
                    "disqualifications": [
                        {
                            "disqualified_from": "2020-01-01",
                            "disqualified_until": "2025-01-01",
                        }
                    ],
                },
                {
                    "forename": "Jane",
                    "surname": "Doe",
                    "disqualifications": [
                        {
                            "disqualified_from": "2019-01-01",
                            "disqualified_until": "2024-01-01",
                        }
                    ],
                },
            ],
            "items_per_page": 50,
            "start_index": 0,
            "total_results": 2,
        }

    def test_create_disqualification_list(self, disqualification_list_data):
        """Test creating a disqualification list."""
        disq_list = DisqualificationList(**disqualification_list_data)
        assert len(disq_list.items) == 2
        assert disq_list.total_results == 2

    def test_has_more_pages_false(self, disqualification_list_data):
        """Test has_more_pages when no more pages."""
        disq_list = DisqualificationList(**disqualification_list_data)
        assert disq_list.has_more_pages is False

    def test_has_more_pages_true(self, disqualification_list_data):
        """Test has_more_pages when more pages exist."""
        disqualification_list_data["total_results"] = 100
        disq_list = DisqualificationList(**disqualification_list_data)
        assert disq_list.has_more_pages is True

    def test_next_start_index(self, disqualification_list_data):
        """Test calculating next start index."""
        disq_list = DisqualificationList(**disqualification_list_data)
        assert disq_list.next_start_index == 50

    def test_empty_disqualification_list(self):
        """Test creating an empty disqualification list."""
        disq_list = DisqualificationList()
        assert disq_list.items == []
        assert disq_list.has_more_pages is False


class TestDisqualificationReason:
    """Test DisqualificationReason enum."""

    def test_misconduct_reason(self):
        """Test misconduct reason."""
        assert DisqualificationReason.MISCONDUCT == "misconduct"

    def test_unfitness_reason(self):
        """Test unfitness reason."""
        assert DisqualificationReason.UNFITNESS == "unfitness"

    def test_fraud_reason(self):
        """Test fraud reason."""
        assert DisqualificationReason.FRAUD == "fraud"

    def test_all_reason_values(self):
        """Test all reason values are unique."""
        reasons = [reason.value for reason in DisqualificationReason]
        assert len(reasons) == len(set(reasons))
