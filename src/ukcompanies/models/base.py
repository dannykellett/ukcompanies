"""Base model with common functionality for all models."""

from typing import Any

from pydantic import BaseModel as PydanticBaseModel
from pydantic import ConfigDict


class BaseModel(PydanticBaseModel):
    """Base model with common configuration for all models."""

    model_config = ConfigDict(
        populate_by_name=True,
        use_enum_values=True,
        validate_assignment=True,
        str_strip_whitespace=True,
        arbitrary_types_allowed=False,
        extra="ignore",  # Allow extra fields from API
    )

    def to_dict(self, exclude_none: bool = True) -> dict[str, Any]:
        """Convert model to dictionary.

        Args:
            exclude_none: Whether to exclude None values

        Returns:
            Dictionary representation of the model
        """
        return self.model_dump(exclude_none=exclude_none)

    def to_json(self, exclude_none: bool = True, indent: int = 2) -> str:
        """Convert model to JSON string.

        Args:
            exclude_none: Whether to exclude None values
            indent: JSON indentation level

        Returns:
            JSON string representation of the model
        """
        return self.model_dump_json(exclude_none=exclude_none, indent=indent)
