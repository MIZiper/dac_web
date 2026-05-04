"""Keycloak authentication module.

Provides JWT token validation and user extraction.
When Keycloak env vars are not set, all functions degrade gracefully
to allow backward-compatible operation without authentication.
"""

import logging
import os
from functools import lru_cache
from typing import Optional

import httpx
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from jose.exceptions import ExpiredSignatureError, JWTClaimsError

logger = logging.getLogger(__name__)

KEYCLOAK_URL = os.getenv("KEYCLOAK_URL", "")
KEYCLOAK_REALM = os.getenv("KEYCLOAK_REALM", "")
KEYCLOAK_CLIENT_ID = os.getenv("KEYCLOAK_CLIENT_ID", "")
KEYCLOAK_CLIENT_SECRET = os.getenv("KEYCLOAK_CLIENT_SECRET", "")


def is_keycloak_enabled() -> bool:
    return bool(KEYCLOAK_URL and KEYCLOAK_REALM and KEYCLOAK_CLIENT_ID)


def get_keycloak_config() -> dict:
    return {
        "keycloak_enabled": is_keycloak_enabled(),
        "keycloak_url": KEYCLOAK_URL,
        "keycloak_realm": KEYCLOAK_REALM,
        "keycloak_client_id": KEYCLOAK_CLIENT_ID,
    }


@lru_cache(maxsize=1)
def _get_jwks() -> dict:
    if not is_keycloak_enabled():
        return {}
    jwks_url = f"{KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}/protocol/openid-connect/certs"
    try:
        with httpx.Client(timeout=10) as client:
            resp = client.get(jwks_url)
            resp.raise_for_status()
            return resp.json()
    except Exception as e:
        logger.error("Failed to fetch JWKS from Keycloak: %s", e)
        return {}


def verify_token(token: str) -> Optional[dict]:
    """Verify a JWT token and return decoded claims, or None if invalid."""
    if not is_keycloak_enabled():
        return None

    jwks = _get_jwks()
    if not jwks:
        return None

    try:
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")

        key = None
        for jwk in jwks.get("keys", []):
            if jwk.get("kid") == kid:
                key = jwk
                break

        if not key:
            logger.warning("No matching JWK found for kid: %s", kid)
            return None

        payload = jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            audience=KEYCLOAK_CLIENT_ID,
            issuer=f"{KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}",
            options={"verify_aud": True, "verify_exp": True},
        )
        return payload

    except ExpiredSignatureError:
        logger.warning("Token has expired")
        return None
    except (JWTError, JWTClaimsError) as e:
        logger.warning("JWT validation failed: %s", e)
        return None
    except Exception as e:
        logger.error("Unexpected error verifying token: %s", e)
        return None


http_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(http_bearer),
) -> Optional[dict]:
    """FastAPI dependency: extract current user from Bearer token.

    Returns user info dict with 'sub' and 'preferred_username' when Keycloak
    is enabled and a valid token is provided.

    Returns None when:
    - Keycloak is disabled (backward compatibility)
    - No token is provided

    Raises HTTPException(401) when Keycloak is enabled but the token is invalid.
    """
    if not is_keycloak_enabled():
        return None

    if credentials is None:
        return None

    token = credentials.credentials
    payload = verify_token(token)

    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return {
        "sub": payload.get("sub"),
        "preferred_username": payload.get("preferred_username", ""),
    }
