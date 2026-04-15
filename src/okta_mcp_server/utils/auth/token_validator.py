import time

import jwt
from jwt import InvalidTokenError, PyJWKClient
from loguru import logger

# Module-level cache: one PyJWKClient per JWKS URL (keys are rotated infrequently).
_jwks_clients: dict[str, PyJWKClient] = {}


def _get_jwks_client(jwks_url: str) -> PyJWKClient:
    if jwks_url not in _jwks_clients:
        _jwks_clients[jwks_url] = PyJWKClient(jwks_url, cache_keys=True)
    return _jwks_clients[jwks_url]


def validate_okta_token(token: str, org_url: str) -> dict:
    """Validate an Okta access token via JWKS and return its claims.

    Checks: RS256 signature (via Okta's public JWKS endpoint) and expiry.
    Audience validation is intentionally skipped because tokens issued by the
    Okta org authorization server carry the org URL as their audience, which
    differs from tokens issued by a custom authorization server. Okta's own
    API enforces audience-level restrictions at call time.

    Raises ValueError if the token is invalid, expired, or cannot be verified.
    """
    org_url = org_url.rstrip("/")
    jwks_url = f"{org_url}/oauth2/v1/keys"

    try:
        client = _get_jwks_client(jwks_url)
        signing_key = client.get_signing_key_from_jwt(token)

        claims = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            options={
                "verify_aud": False,
                "verify_exp": True,
            },
            leeway=30,  # tolerate up to 30s clock skew between Okta and this server
        )

        logger.debug(
            f"Token validated: sub={claims.get('sub', 'unknown')}, "
            f"exp={claims.get('exp', 0)}"
        )
        return claims

    except jwt.ExpiredSignatureError as exc:
        raise ValueError("Token has expired") from exc
    except (InvalidTokenError, Exception) as exc:
        raise ValueError(f"Token validation failed: {exc}") from exc


def get_token_groups(token: str) -> list[str]:
    """Extract the groups claim from a token without re-validating the signature.

    Returns an empty list if the claim is absent or the token cannot be decoded.
    Token must already have been validated via validate_okta_token().
    """
    try:
        claims = jwt.decode(
            token,
            options={"verify_signature": False},
            algorithms=["RS256"],
        )
        groups = claims.get("groups", [])
        return groups if isinstance(groups, list) else []
    except Exception:
        return []


def is_token_expiring_soon(token: str, buffer_seconds: int = 60) -> bool:
    """Return True if the token expires within buffer_seconds.

    Uses no-signature decode for speed (token was already validated at connection time).
    Returns True (treat-as-expired) if the token cannot be decoded.
    """
    try:
        claims = jwt.decode(
            token,
            options={"verify_signature": False},
            algorithms=["RS256"],
        )
        exp = claims.get("exp", 0)
        return exp < (time.time() + buffer_seconds)
    except Exception:
        return True
