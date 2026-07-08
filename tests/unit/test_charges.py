"""Unit tests for charge models and charge endpoints."""

from datetime import date

import pytest
import respx
from httpx import Response

from ukcompanies import AsyncClient
from ukcompanies.exceptions import NotFoundError, ValidationError
from ukcompanies.models.charge import (
    Charge,
    ChargeClassification,
    ChargeList,
    ChargeStatus,
    ChargeTransaction,
    PersonEntitled,
)

BASE_URL = "https://api.company-information.service.gov.uk"


# Realistic charges list fixture, shaped like the Companies House charges resource.
CHARGES_LIST_FIXTURE = {
    "etag": "abc123def456",
    "total_count": 2,
    "unfiled_count": 0,
    "satisfied_count": 1,
    "part_satisfied_count": 0,
    "items": [
        {
            "charge_id": "AbC1dEfGhIjKlMnOpQrStUvWxYz",
            "charge_code": "001234560001",
            "charge_number": 1,
            "classification": {
                "type": "charge-description",
                "description": "A registered charge",
            },
            "status": "outstanding",
            "created_on": "2023-05-01",
            "delivered_on": "2023-05-08",
            "particulars": {
                "type": "brief-description",
                "description": "The freehold property known as 1 Example Street.",
                "contains_fixed_charge": True,
                "contains_floating_charge": False,
                "contains_negative_pledge": True,
            },
            "secured_details": {
                "type": "amount-secured",
                "description": "All monies due or to become due.",
            },
            "persons_entitled": [
                {"name": "Big Bank PLC"},
            ],
            "transactions": [
                {
                    "transaction_id": "MzM2NTY5MzQ1OGFkaXF6a2N4",
                    "filing_type": "create-charge",
                    "delivered_on": "2023-05-08",
                    "links": {
                        "filing": "/company/12345678/filing-history/MzM2NTY5MzQ1OGFkaXF6a2N4"
                    },
                }
            ],
            "links": {
                "self": "/company/12345678/charges/AbC1dEfGhIjKlMnOpQrStUvWxYz"
            },
        },
        {
            "charge_id": "ZyXwVuTsRqPoNmLkJiHgFeDcBa",
            "charge_code": "001234560002",
            "charge_number": 2,
            "classification": {
                "type": "charge-description",
                "description": "A registered charge",
            },
            "status": "fully-satisfied",
            "created_on": "2020-01-10",
            "delivered_on": "2020-01-15",
            "satisfied_on": "2022-11-30",
            "persons_entitled": [
                {"name": "Small Lender Ltd"},
            ],
            "links": {
                "self": "/company/12345678/charges/ZyXwVuTsRqPoNmLkJiHgFeDcBa"
            },
        },
    ],
}


class TestChargeStatus:
    """Test ChargeStatus enum."""

    def test_charge_status_values(self):
        """Test that charge statuses have correct values."""
        assert ChargeStatus.OUTSTANDING.value == "outstanding"
        assert ChargeStatus.FULLY_SATISFIED.value == "fully-satisfied"
        assert ChargeStatus.PART_SATISFIED.value == "part-satisfied"
        assert ChargeStatus.SATISFIED.value == "satisfied"

    def test_charge_status_from_string(self):
        """Test creating status from string."""
        assert ChargeStatus("outstanding") == ChargeStatus.OUTSTANDING


class TestChargeModel:
    """Test parsing the Charge / ChargeList models from realistic JSON."""

    def test_charge_list_parses_fixture(self):
        """Test that a realistic charges payload parses fully."""
        charge_list = ChargeList(**CHARGES_LIST_FIXTURE)

        assert charge_list.total_count == 2
        assert charge_list.satisfied_count == 1
        assert charge_list.unfiled_count == 0
        assert charge_list.etag == "abc123def456"
        assert len(charge_list.items) == 2

        first = charge_list.items[0]
        assert isinstance(first, Charge)
        # charge_id is aliased to id
        assert first.id == "AbC1dEfGhIjKlMnOpQrStUvWxYz"
        assert first.charge_code == "001234560001"
        assert first.charge_number == 1
        assert first.status == "outstanding"
        assert first.created_on == date(2023, 5, 1)
        assert first.delivered_on == date(2023, 5, 8)
        assert first.satisfied_on is None

        assert isinstance(first.classification, ChargeClassification)
        assert first.classification.classification_type == "charge-description"
        assert first.classification.description == "A registered charge"

        assert first.particulars.contains_fixed_charge is True
        assert first.particulars.contains_floating_charge is False
        assert first.secured_details.description == "All monies due or to become due."

        assert first.persons_entitled == [PersonEntitled(name="Big Bank PLC")]

        assert len(first.transactions) == 1
        txn = first.transactions[0]
        assert isinstance(txn, ChargeTransaction)
        assert txn.transaction_id == "MzM2NTY5MzQ1OGFkaXF6a2N4"
        assert txn.filing_type == "create-charge"
        assert txn.delivered_on == date(2023, 5, 8)

        assert first.links.self == "/company/12345678/charges/AbC1dEfGhIjKlMnOpQrStUvWxYz"

        second = charge_list.items[1]
        assert second.status == "fully-satisfied"
        assert second.satisfied_on == date(2022, 11, 30)
        # Missing optional keys stay None / empty.
        assert second.particulars is None
        assert second.transactions is None

    def test_charge_list_empty(self):
        """Test that an empty list is tolerated with sensible defaults."""
        charge_list = ChargeList()
        assert charge_list.items == []
        assert charge_list.total_count == 0
        assert charge_list.satisfied_count is None

    def test_charge_tolerates_missing_keys(self):
        """Test that a sparse charge (only id) parses without error."""
        charge = Charge(charge_id="XYZ")
        assert charge.id == "XYZ"
        assert charge.status is None
        assert charge.created_on is None
        assert charge.persons_entitled is None


@pytest.mark.asyncio
class TestListCharges:
    """Test the list_charges endpoint."""

    async def test_list_charges_success(self):
        """Test successful charges listing (mocked)."""
        async with AsyncClient(api_key="test_key") as client:
            with respx.mock:
                route = respx.get(f"{BASE_URL}/company/12345678/charges").mock(
                    return_value=Response(200, json=CHARGES_LIST_FIXTURE)
                )

                result = await client.list_charges("12345678")

                assert route.called
                assert route.call_count == 1
                assert isinstance(result, ChargeList)
                assert result.total_count == 2
                assert len(result.items) == 2
                assert result.items[0].id == "AbC1dEfGhIjKlMnOpQrStUvWxYz"
                assert result.items[0].status == "outstanding"
                assert result.items[1].status == "fully-satisfied"

    async def test_list_charges_not_found(self):
        """Test list_charges raises NotFoundError for an unknown company."""
        async with AsyncClient(api_key="test_key") as client:
            with respx.mock:
                route = respx.get(f"{BASE_URL}/company/99999999/charges").mock(
                    return_value=Response(
                        404, json={"error": "company-profile-not-found"}
                    )
                )

                with pytest.raises(NotFoundError) as exc_info:
                    await client.list_charges("99999999")

                assert route.called
                assert "not found" in str(exc_info.value).lower()


@pytest.mark.asyncio
class TestGetCharge:
    """Test the get_charge endpoint."""

    async def test_get_charge_success(self):
        """Test successful single-charge retrieval (mocked)."""
        charge_fixture = CHARGES_LIST_FIXTURE["items"][0]
        charge_id = charge_fixture["charge_id"]

        async with AsyncClient(api_key="test_key") as client:
            with respx.mock:
                route = respx.get(
                    f"{BASE_URL}/company/12345678/charges/{charge_id}"
                ).mock(return_value=Response(200, json=charge_fixture))

                result = await client.get_charge("12345678", charge_id)

                assert route.called
                assert isinstance(result, Charge)
                assert result.id == charge_id
                assert result.charge_code == "001234560001"
                assert result.status == "outstanding"
                assert result.classification.description == "A registered charge"

    async def test_get_charge_not_found(self):
        """Test get_charge raises NotFoundError for an unknown charge."""
        async with AsyncClient(api_key="test_key") as client:
            with respx.mock:
                route = respx.get(
                    f"{BASE_URL}/company/12345678/charges/does-not-exist"
                ).mock(return_value=Response(404, json={"error": "charge-not-found"}))

                with pytest.raises(NotFoundError):
                    await client.get_charge("12345678", "does-not-exist")

                assert route.called

    async def test_get_charge_empty_id_raises(self):
        """Test that an empty charge ID raises ValidationError before any request."""
        async with AsyncClient(api_key="test_key") as client:
            with pytest.raises(ValidationError):
                await client.get_charge("12345678", "   ")
