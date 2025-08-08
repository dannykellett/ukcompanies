"""Authentication handler for UK Companies API."""

import base64

from .exceptions import AuthenticationError


class AuthHandler:
    """Handles authentication for the Companies House API.

    The API uses HTTP Basic Authentication with the API key as the username
    and an empty password.
    """

    def __init__(self, api_key: str) -> None:
        """Initialize the authentication handler.

        Args:
            api_key: API key for authentication

        Raises:
            AuthenticationError: If API key is invalid
        """
        if not api_key or not api_key.strip():
            raise AuthenticationError("API key is required for authentication")

        self.api_key = api_key.strip()
        self._auth_header = self._generate_auth_header()

    def _generate_auth_header(self) -> str:
        """Generate the HTTP Basic Auth header value.

        Returns:
            Base64 encoded authentication string
        """
        # Companies House uses API key as username with empty password
        auth_string = f"{self.api_key}:"
        auth_bytes = auth_string.encode("utf-8")
        auth_b64 = base64.b64encode(auth_bytes).decode("ascii")
        return f"Basic {auth_b64}"

    def get_headers(self) -> dict[str, str]:
        """Get authentication headers for requests.

        Returns:
            Dictionary with Authorization header
        """
        return {"Authorization": self._auth_header}

    def validate_api_key_format(self) -> bool:
        """Validate the API key format.

        Companies House API keys are typically 32+ characters.

        Returns:
            True if API key appears valid
        """
        # Basic validation - API keys should be at least 20 chars
        if len(self.api_key) < 20:
            return False

        # Check for common invalid patterns
        return self.api_key.lower() not in ["test", "demo", "example", "your-api-key"]
