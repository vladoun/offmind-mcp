"""Firebase Authentication client for MCP."""

import json
import os
import time
import secrets
import webbrowser
import threading
from pathlib import Path
from typing import Optional
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, urlencode

import httpx


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """HTTP handler for OAuth callback."""

    def do_GET(self):
        """Handle GET request with OAuth callback."""
        # Parse query parameters
        parsed_path = urlparse(self.path)
        params = parse_qs(parsed_path.query)

        # Store the result in server
        self.server.oauth_result = {
            'code': params.get('code', [None])[0],
            'state': params.get('state', [None])[0],
            'error': params.get('error', [None])[0]
        }

        # Send success response
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Authentication Successful</title>
            <style>
                body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                       display: flex; align-items: center; justify-content: center;
                       height: 100vh; margin: 0; background: #f5f5f5; }
                .container { text-align: center; background: white; padding: 40px;
                            border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                .checkmark { font-size: 64px; color: #4CAF50; }
                h1 { color: #333; margin: 20px 0 10px; }
                p { color: #666; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="checkmark">✓</div>
                <h1>Authentication Successful!</h1>
                <p>You can close this window and return to Claude Desktop.</p>
            </div>
        </body>
        </html>
        """
        self.wfile.write(html.encode())

    def log_message(self, format, *args):
        """Suppress log messages."""
        pass


class OAuthCallbackServer(HTTPServer):
    """HTTP server for receiving OAuth callback."""

    def __init__(self, port=8888):
        super().__init__(('localhost', port), OAuthCallbackHandler)
        self.oauth_result = None


class FirebaseAuthManager:
    """Manages Firebase Authentication for MCP client."""

    def __init__(self, api_key: str, api_url: str):
        """Initialize Firebase Auth manager.

        Args:
            api_key: Firebase Web API Key
            api_url: Proxy API URL
        """
        self.api_key = api_key
        self.api_url = api_url
        self.token_file = Path.home() / ".offmind" / "token.json"
        self.token_file.parent.mkdir(parents=True, exist_ok=True)

    def get_id_token(self) -> Optional[str]:
        """Get valid Firebase ID token, refreshing if needed.

        Returns:
            Firebase ID token or None if not authenticated
        """
        if not self.token_file.exists():
            return None

        try:
            with open(self.token_file) as f:
                token_data = json.load(f)

            id_token = token_data.get('idToken')
            refresh_token = token_data.get('refreshToken')
            expires_at = token_data.get('expiresAt', 0)

            # Check if token is still valid (with 5 min buffer)
            if time.time() < expires_at - 300:
                return id_token

            # Token expired, try to refresh
            if refresh_token:
                try:
                    return self.refresh_id_token(refresh_token)
                except Exception as e:
                    print(f"Failed to refresh token: {e}")
                    return None

            return None

        except (json.JSONDecodeError, ValueError, KeyError):
            return None

    def refresh_id_token(self, refresh_token: str) -> str:
        """Refresh Firebase ID token using refresh token.

        Args:
            refresh_token: Firebase refresh token

        Returns:
            New Firebase ID token

        Raises:
            Exception: If refresh fails
        """
        url = f"https://securetoken.googleapis.com/v1/token?key={self.api_key}"

        response = httpx.post(url, json={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token
        }, timeout=10.0)
        response.raise_for_status()

        data = response.json()
        id_token = data['id_token']
        new_refresh_token = data['refresh_token']
        expires_in = int(data['expires_in'])

        # Save new tokens
        self.save_tokens(id_token, new_refresh_token, expires_in)
        return id_token

    def sign_in_with_custom_token(self, custom_token: str) -> str:
        """Sign in with Firebase custom token (for testing).

        Args:
            custom_token: Firebase custom token

        Returns:
            Firebase ID token
        """
        url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithCustomToken?key={self.api_key}"

        response = httpx.post(url, json={
            "token": custom_token,
            "returnSecureToken": True
        }, timeout=10.0)
        response.raise_for_status()

        data = response.json()
        id_token = data['idToken']
        refresh_token = data['refreshToken']
        expires_in = int(data['expiresIn'])

        self.save_tokens(id_token, refresh_token, expires_in)
        return id_token

    def oauth_sign_in(self) -> str:
        """Sign in with Google OAuth via browser.

        Returns:
            Firebase ID token

        Raises:
            Exception: If authentication fails
        """
        # Start local callback server
        server = OAuthCallbackServer(port=8888)
        server_thread = threading.Thread(target=server.serve_forever)
        server_thread.daemon = True
        server_thread.start()

        # Generate state for CSRF protection
        state = secrets.token_urlsafe(32)

        # Build landing page URL with OAuth parameters
        oauth_params = {
            'state': state,
            'redirect_uri': 'http://localhost:8888'
        }
        landing_url = f"{self.api_url}/?{urlencode(oauth_params)}"

        print("\n🔐 Opening browser for authentication...")
        print(f"If the browser doesn't open, visit: {landing_url}\n")
        webbrowser.open(landing_url)

        print("⏳ Waiting for authentication (this may take a minute)...")

        # Wait for callback (timeout after 2 minutes)
        timeout = time.time() + 120
        while server.oauth_result is None and time.time() < timeout:
            time.sleep(0.5)

        server.shutdown()

        if server.oauth_result is None:
            raise Exception("Authentication timed out")

        if server.oauth_result.get('error'):
            raise Exception(f"OAuth error: {server.oauth_result['error']}")

        if server.oauth_result.get('state') != state:
            raise Exception("Invalid state - possible CSRF attack")

        auth_code = server.oauth_result.get('code')
        if not auth_code:
            raise Exception("No authorization code received")

        # Exchange code for Firebase tokens via proxy API
        return self.exchange_code_for_tokens(auth_code)

    def exchange_code_for_tokens(self, auth_code: str) -> str:
        """Exchange OAuth code for Firebase ID token via proxy API.

        Args:
            auth_code: OAuth authorization code

        Returns:
            Firebase ID token

        Raises:
            Exception: If exchange fails
        """
        url = f"{self.api_url}/auth/oauth/exchange"

        response = httpx.post(url, json={
            "code": auth_code,
            "redirect_uri": "http://localhost:8888/callback"
        }, timeout=30.0)
        response.raise_for_status()

        data = response.json()
        id_token = data['idToken']
        refresh_token = data['refreshToken']
        expires_in = int(data['expiresIn'])
        user_info = data.get('user', {})

        # Save tokens
        self.save_tokens(id_token, refresh_token, expires_in)

        print(f"\n✓ Successfully signed in as: {user_info.get('email', 'User')}")
        return id_token

    def save_tokens(self, id_token: str, refresh_token: str, expires_in: int):
        """Save Firebase tokens to local file.

        Args:
            id_token: Firebase ID token
            refresh_token: Firebase refresh token
            expires_in: Token expiration time in seconds
        """
        expires_at = time.time() + expires_in

        token_data = {
            "idToken": id_token,
            "refreshToken": refresh_token,
            "expiresAt": expires_at
        }

        with open(self.token_file, 'w') as f:
            json.dump(token_data, f, indent=2)

        # Set restrictive permissions
        os.chmod(self.token_file, 0o600)

    def clear_tokens(self):
        """Clear stored tokens."""
        if self.token_file.exists():
            self.token_file.unlink()

    def ensure_authenticated(self) -> str:
        """Ensure user is authenticated with Firebase.

        Returns:
            Valid Firebase ID token

        Raises:
            Exception: If authentication fails
        """
        # Try to get existing valid token
        id_token = self.get_id_token()
        if id_token:
            return id_token

        # No valid token - start OAuth flow
        print("\n⚠️  No valid authentication found")
        return self.oauth_sign_in()
