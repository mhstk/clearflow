"""
Google OAuth service for authentication.

Handles the OAuth flow with Google including:
- Exchanging authorization codes for tokens
- Fetching user profile information
"""

import httpx
from typing import Optional, Dict
from urllib.parse import urlencode

from app.core.config import settings

# Google OAuth endpoints
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"


def get_google_auth_url() -> Optional[str]:
    """
    Generate the Google OAuth authorization URL.

    Returns:
        The authorization URL or None if Google OAuth is not configured
    """
    if not settings.GOOGLE_CLIENT_ID:
        return None

    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "consent"
    }

    return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"


async def exchange_code_for_tokens(code: str) -> Optional[Dict]:
    """
    Exchange an authorization code for access tokens.

    Args:
        code: The authorization code from Google

    Returns:
        Token response dict or None if exchange failed
    """
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        return None

    async with httpx.AsyncClient() as client:
        response = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code"
            }
        )

        if response.status_code == 200:
            return response.json()

        return None


async def get_google_user_info(access_token: str) -> Optional[Dict]:
    """
    Fetch user profile information from Google.

    Args:
        access_token: The access token from Google

    Returns:
        User info dict containing id, email, name, picture, or None if failed
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"}
        )

        if response.status_code == 200:
            return response.json()

        return None
