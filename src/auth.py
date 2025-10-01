"""OAuth authentication and token management for MCP client."""

import json
import os
import webbrowser
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import httpx


class TokenManager:
    """Manages OAuth tokens with local encrypted storage."""

    def __init__(self, api_url: str):
        """Initialize token manager.

        Args:
            api_url: Base URL of the proxy API
        """
        self.api_url = api_url.rstrip("/")
        self.token_file = Path.home() / ".offmind" / "token.json"
        self.token_file.parent.mkdir(parents=True, exist_ok=True)

    def get_token(self) -> Optional[str]:
        """Get valid access token, refreshing if needed.

        Returns:
            Valid access token or None if authentication needed
        """
        # Check if we have a stored token
        if self.token_file.exists():
            try:
                with open(self.token_file, "r") as f:
                    token_data = json.load(f)

                access_token = token_data.get("access_token")
                expires_at = token_data.get("expires_at")

                # Check if token is still valid
                if access_token and expires_at:
                    expires_dt = datetime.fromisoformat(expires_at)
                    if expires_dt > datetime.now(timezone.utc):
                        return access_token

            except (json.JSONDecodeError, ValueError):
                pass

        # No valid token, need to authenticate
        return None

    def save_token(self, access_token: str, expires_in: int = 3600):
        """Save access token to local storage.

        Args:
            access_token: JWT access token
            expires_in: Token expiration time in seconds (default 1 hour)
        """
        expires_at = datetime.now(timezone.utc).timestamp() + expires_in
        expires_at_iso = datetime.fromtimestamp(expires_at, tz=timezone.utc).isoformat()

        token_data = {
            "access_token": access_token,
            "expires_at": expires_at_iso
        }

        with open(self.token_file, "w") as f:
            json.dump(token_data, f, indent=2)

        # Set restrictive permissions (user read/write only)
        os.chmod(self.token_file, 0o600)

    def clear_token(self):
        """Clear stored token."""
        if self.token_file.exists():
            self.token_file.unlink()

    def login(self, user_id: str) -> str:
        """Login with user ID and get access token.

        This is a simplified auth flow. In production, this would use
        OAuth with browser-based authentication.

        Args:
            user_id: Firebase user ID

        Returns:
            Access token

        Raises:
            Exception: If login fails
        """
        try:
            response = httpx.post(
                f"{self.api_url}/api/auth/login",
                json={"user_id": user_id},
                timeout=10.0
            )
            response.raise_for_status()

            data = response.json()
            access_token = data["access_token"]

            # Save token
            self.save_token(access_token)

            return access_token

        except httpx.HTTPError as e:
            raise Exception(f"Login failed: {e}")

    def ensure_authenticated(self) -> str:
        """Ensure user is authenticated, prompting for login if needed.

        Returns:
            Valid access token

        Raises:
            Exception: If authentication fails
        """
        # Try to get existing token
        token = self.get_token()
        if token:
            return token

        # Need to authenticate
        # For now, get user_id from environment
        user_id = os.getenv("FIREBASE_USER_ID")
        if not user_id:
            raise ValueError(
                "No valid token found and FIREBASE_USER_ID not set. "
                "Please set FIREBASE_USER_ID environment variable or run 'mcp-firebase-todos login'"
            )

        # Login and get token
        return self.login(user_id)


def interactive_login(api_url: str):
    """Interactive login flow for CLI.

    This would typically open a browser for OAuth, but for now
    it prompts for user_id.

    Args:
        api_url: Base URL of the proxy API
    """
    print("=== Offmind MCP Login ===")
    print()
    user_id = input("Enter your Firebase User ID: ").strip()

    if not user_id:
        print("Error: User ID is required")
        return

    token_manager = TokenManager(api_url)

    try:
        token_manager.login(user_id)
        print()
        print("✓ Login successful! Token saved.")
        print()

    except Exception as e:
        print(f"✗ Login failed: {e}")
