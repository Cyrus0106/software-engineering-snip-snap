import json
import os
import ssl
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import jwt
from jwt import PyJWKClient

try:
    import certifi
except ImportError:
    certifi = None

_JWK_CLIENT = None
_JWK_URL = None


def _build_ssl_context():
    if certifi is not None:
        return ssl.create_default_context(cafile=certifi.where())
    return ssl.create_default_context()


def _get_jwk_client() -> PyJWKClient:
    global _JWK_CLIENT, _JWK_URL

    supabase_url = os.environ["SUPABASE_URL"].rstrip("/")
    jwk_url = f"{supabase_url}/auth/v1/.well-known/jwks.json"

    if _JWK_CLIENT is None or _JWK_URL != jwk_url:
        _JWK_CLIENT = PyJWKClient(jwk_url)
        _JWK_URL = jwk_url

    return _JWK_CLIENT


def _fetch_supabase_user(access_token: str) -> dict:
    supabase_url = os.environ["SUPABASE_URL"].rstrip("/")
    anon_key = os.environ["SUPABASE_ANON_KEY"]
    request = Request(
        f"{supabase_url}/auth/v1/user",
        headers={
            "Authorization": f"Bearer {access_token}",
            "apikey": anon_key,
        },
    )

    try:
        with urlopen(request, timeout=10, context=_build_ssl_context()) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        details = exc.read().decode("utf-8", errors="ignore")
        raise ValueError(f"Supabase auth validation failed: {exc.code} {details}") from exc
    except URLError as exc:
        raise ValueError(f"Supabase auth validation failed: {exc.reason}") from exc

    issuer = f"{supabase_url}/auth/v1"
    return {
        "sub": payload.get("id"),
        "email": payload.get("email"),
        "aud": payload.get("aud") or "authenticated",
        "iss": payload.get("app_metadata", {}).get("issuer", issuer),
    }


def verify_supabase_jwt(access_token: str) -> dict:
    supabase_url = os.environ["SUPABASE_URL"].rstrip("/")
    issuer = f"{supabase_url}/auth/v1"

    header = jwt.get_unverified_header(access_token)
    print("JWT header:", header)

    # Peek claims without verifying signature, just to inspect aud
    peek = jwt.decode(access_token, options={"verify_signature": False})
    print("JWT aud (peek):", peek.get("aud"), "iss:", peek.get("iss"))

    try:
        jwk_client = _get_jwk_client()
        signing_key = jwk_client.get_signing_key_from_jwt(access_token)

        allowed_algs = ["ES256", "RS256", "EdDSA"]

        allowed_audiences = ["authenticated", "anon"]
        print("Allowed audiences:", allowed_audiences)

        return jwt.decode(
            access_token,
            signing_key.key,
            algorithms=allowed_algs,
            issuer=issuer,
            audience=allowed_audiences,
            options={"require": ["exp", "iss", "aud"]},
        )
    except Exception as exc:
        print("JWK verification failed, falling back to Supabase user lookup:", repr(exc))
        claims = _fetch_supabase_user(access_token)

        if claims.get("iss") != issuer:
            raise ValueError("Supabase auth validation failed: invalid issuer")
        if not claims.get("sub"):
            raise ValueError("Supabase auth validation failed: missing user id")

        return claims