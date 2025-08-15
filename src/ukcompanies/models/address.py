"""Address model for UK Companies API."""

from pydantic import Field

from .base import BaseModel


class Address(BaseModel):
    """Represents a UK address."""

    premises: str | None = Field(None, description="Building name or number")
    address_line_1: str | None = Field(None, description="First line of address")
    address_line_2: str | None = Field(None, description="Second line of address")
    locality: str | None = Field(None, description="Town or city")
    region: str | None = Field(None, description="County or state")
    postal_code: str | None = Field(None, description="Postcode")
    country: str | None = Field(None, description="Country name")

    @property
    def full_address(self) -> str:
        """Get the full address as a formatted string.

        Returns:
            Formatted address string
        """
        parts = []

        if self.premises:
            parts.append(self.premises)

        if self.address_line_1:
            parts.append(self.address_line_1)

        if self.address_line_2:
            parts.append(self.address_line_2)

        if self.locality:
            parts.append(self.locality)

        if self.region:
            parts.append(self.region)

        if self.postal_code:
            parts.append(self.postal_code)

        if self.country:
            parts.append(self.country)

        return ", ".join(parts)
