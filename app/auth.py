"""
JWT verification for Supabase Auth tokens.

Provides :func:`verify_supabase_jwt` which validates an access token issued
by Supabase Auth using the project's JWKS endpoint.
"""

import os
import jwt
from jwt import PyJWKClient

_JWK_CLIENT = None
_JWK_URL = None


def _get_jwk_client() -> PyJWKClient:
    global _JWK_CLIENT, _JWK_URL

    supabase_url = os.environ["SUPABASE_URL"].rstrip("/")
    jwk_url = f"{supabase_url}/auth/v1/.well-known/jwks.json"

    if _JWK_CLIENT is None or _JWK_URL != jwk_url:
        _JWK_CLIENT = PyJWKClient(jwk_url)
        _JWK_URL = jwk_url

    return _JWK_CLIENT


def verify_supabase_jwt(access_token: str) -> dict:
    """
    Verify a Supabase-issued JWT and return its decoded claims.

    Args:
        access_token: The raw JWT string from the Supabase Auth client.

    Returns:
        A dict of verified JWT claims (``sub``, ``email``, ``role``, etc.).

    Raises:
        jwt.exceptions.InvalidTokenError: If the token is expired, has a bad
            signature, or fails audience/issuer checks.
    """
    supabase_url = os.environ["SUPABASE_URL"].rstrip("/")
    issuer = f"{supabase_url}/auth/v1"

    header = jwt.get_unverified_header(access_token)
    print("JWT header:", header)

    # Peek claims without verifying signature, just to inspect aud
    peek = jwt.decode(access_token, options={"verify_signature": False})
    print("JWT aud (peek):", peek.get("aud"), "iss:", peek.get("iss"))

    jwk_client = _get_jwk_client()
    signing_key = jwk_client.get_signing_key_from_jwt(access_token)

    allowed_algs = ["ES256", "RS256", "EdDSA"]

    # Accept common Supabase audiences. Adjust if peek shows something else.
    allowed_audiences = ["authenticated", "anon"]
    print("Allowed audiences:", allowed_audiences)

    claims = jwt.decode(
        access_token,
        signing_key.key,
        algorithms=allowed_algs,
        issuer=issuer,
        audience=allowed_audiences,
        options={"require": ["exp", "iss", "aud"]},
    )
    return claims