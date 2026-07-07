"""Charge (company mortgages/charges) models for UK Companies API."""

from datetime import date
from enum import Enum
from typing import Any

from pydantic import Field

from .base import BaseModel


class ChargeStatus(str, Enum):
    """Status of a registered charge."""

    OUTSTANDING = "outstanding"
    FULLY_SATISFIED = "fully-satisfied"
    PART_SATISFIED = "part-satisfied"
    SATISFIED = "satisfied"


class ChargeClassification(BaseModel):
    """Classification (type) of a charge."""

    classification_type: str | None = Field(
        None,
        alias="type",
        description="Classification type, e.g. 'charge-description'",
    )
    description: str | None = Field(None, description="Classification description")


class ChargeParticulars(BaseModel):
    """Particulars describing what the charge covers."""

    type: str | None = Field(None, description="Type of particulars")
    description: str | None = Field(None, description="Free-text description")
    contains_fixed_charge: bool | None = Field(
        None, description="Whether a fixed charge is included"
    )
    contains_floating_charge: bool | None = Field(
        None, description="Whether a floating charge is included"
    )
    contains_negative_pledge: bool | None = Field(
        None, description="Whether a negative pledge is included"
    )
    floating_charge_covers_all: bool | None = Field(
        None, description="Whether the floating charge covers all property/undertaking"
    )
    chargor_acting_as_bare_trustee: bool | None = Field(
        None, description="Whether the chargor acts as a bare trustee"
    )


class SecuredDetails(BaseModel):
    """Details of the amount/obligation secured by the charge."""

    type: str | None = Field(None, description="Type of secured details")
    description: str | None = Field(None, description="Description of what is secured")


class PersonEntitled(BaseModel):
    """A person entitled to the charge."""

    name: str | None = Field(None, description="Name of the person entitled")


class ChargeLinks(BaseModel):
    """Links associated with a charge."""

    self: str | None = Field(None, description="Link to this charge resource")
    transactions: str | None = Field(None, description="Link to charge transactions")
    insolvency_cases: str | None = Field(None, description="Link to insolvency cases")


class TransactionLinks(BaseModel):
    """Links for a charge transaction."""

    filing: str | None = Field(None, description="Link to the associated filing")
    insolvency_case: str | None = Field(None, description="Link to insolvency case")


class ChargeTransaction(BaseModel):
    """A transaction (filing event) against a charge."""

    transaction_id: str | None = Field(None, description="Transaction identifier")
    filing_type: str | None = Field(None, description="Filing type of the transaction")
    delivered_on: date | None = Field(None, description="Date the transaction was delivered")
    insolvency_case_number: int | None = Field(
        None, description="Associated insolvency case number"
    )
    links: TransactionLinks | None = Field(None, description="Related links")


class InsolvencyCase(BaseModel):
    """An insolvency case linked to a charge."""

    case_number: int | None = Field(None, description="Insolvency case number")
    case_type: str | None = Field(None, description="Type of insolvency case")
    description: str | None = Field(None, description="Case description")
    links: dict[str, Any] | None = Field(None, description="Related links")


class Charge(BaseModel):
    """A single registered charge (mortgage) against a company."""

    id: str | None = Field(None, alias="charge_id", description="Charge identifier")
    charge_code: str | None = Field(None, description="Charge code")
    charge_number: int | None = Field(None, description="Sequential charge number")
    classification: ChargeClassification | None = Field(
        None, description="Charge classification"
    )
    status: ChargeStatus | None = Field(None, description="Status of the charge")
    assets_ceased_released: str | None = Field(
        None, description="Reason assets ceased to be / were released"
    )
    acquired_on: date | None = Field(None, description="Date the charge was acquired")
    created_on: date | None = Field(None, description="Date the charge was created")
    delivered_on: date | None = Field(None, description="Date the charge was delivered")
    resolved_on: date | None = Field(None, description="Date the charge was resolved")
    covering_instrument_date: date | None = Field(
        None, description="Date of the covering instrument"
    )
    satisfied_on: date | None = Field(None, description="Date the charge was satisfied")
    particulars: ChargeParticulars | None = Field(
        None, description="Particulars of the charge"
    )
    secured_details: SecuredDetails | None = Field(
        None, description="Details of the secured obligation"
    )
    scottish_alterations: dict[str, Any] | None = Field(
        None, description="Scottish alteration details"
    )
    more_than_four_persons_entitled: bool | None = Field(
        None, description="Whether more than four persons are entitled"
    )
    persons_entitled: list[PersonEntitled] | None = Field(
        None, description="Persons entitled to the charge"
    )
    transactions: list[ChargeTransaction] | None = Field(
        None, description="Transactions against the charge"
    )
    insolvency_cases: list[InsolvencyCase] | None = Field(
        None, description="Insolvency cases linked to the charge"
    )
    links: ChargeLinks | None = Field(None, description="Related links")


class ChargeList(BaseModel):
    """Paginated list of charges for a company."""

    etag: str | None = Field(None, description="ETag for the resource")
    total_count: int = Field(0, description="Total number of charges")
    unfiled_count: int | None = Field(None, description="Number of unfiled charges")
    satisfied_count: int | None = Field(None, description="Number of satisfied charges")
    part_satisfied_count: int | None = Field(
        None, description="Number of part-satisfied charges"
    )
    items: list[Charge] = Field(default_factory=list, description="List of charges")
