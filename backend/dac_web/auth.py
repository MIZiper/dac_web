"""Keycloak authentication module.

Provides JWT token validation and user extraction.
When Keycloak env vars are not set, all functions degrade gracefully
to allow backward-compatible operation without authentication.
"""

import logging
from typing import Optional

import httpx
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from jose.exceptions import ExpiredSignatureError, JWTClaimsError

from dac_web.config import settings

logger = logging.getLogger(__name__)


def is_keycloak_enabled() -> bool:
    return bool(settings.keycloak_url and settings.keycloak_realm and settings.keycloak_client_id)


def get_keycloak_config() -> dict:
    return {
        "keycloak_enabled": is_keycloak_enabled(),
        "keycloak_url": settings.keycloak_url_public,
        "keycloak_realm": settings.keycloak_realm,
        "keycloak_client_id": settings.keycloak_client_id,
    }


_jwks_cache: dict | None = None


async def _get_jwks() -> dict:
    global _jwks_cache
    if _jwks_cache is not None:
        return _jwks_cache
    if not is_keycloak_enabled():
        _jwks_cache = {}
        return _jwks_cache
    jwks_url = f"{settings.keycloak_url}/realms/{settings.keycloak_realm}/protocol/openid-connect/certs"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(jwks_url)
            resp.raise_for_status()
            _jwks_cache = resp.json()
            return _jwks_cache
    except Exception as e:
        logger.error("Failed to fetch JWKS from Keycloak: %s", e)
        _jwks_cache = {}
        return _jwks_cache


async def verify_token(token: str) -> Optional[dict]:
    """Verify a JWT token and return decoded claims, or None if invalid."""
    if not is_keycloak_enabled():
        return None

    jwks = await _get_jwks()
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
            audience="account",  # all users can interact, further permission control to be defined
            issuer=f"{settings.keycloak_url_public}/realms/{settings.keycloak_realm}",
            options={"verify_aud": True, "verify_exp": True},  # TODO: ask frontend to refresh token if expires
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
    payload = await verify_token(token)

    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return {
        "sub": payload.get("sub"),
        "preferred_username": payload.get("preferred_username", ""),
        "given_name": payload.get("given_name", ""),
        "family_name": payload.get("family_name", ""),
    }


async def require_admin(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(http_bearer),
) -> None:
    """FastAPI dependency: require admin access.

    - Keycloak enabled: checks token has settings.admin_role in client or realm roles.
    - Keycloak disabled + admin_token set: checks X-Admin-Token header.
    - Keycloak disabled + admin_token empty: allows all (dev mode).

    Raises HTTPException(403) on failure, HTTPException(401) if auth required but missing.
    """
    if is_keycloak_enabled():
        if credentials is None:
            raise HTTPException(status_code=401, detail="Authentication required")
        token = credentials.credentials
        payload = await verify_token(token)
        if payload is None:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        resource_access = payload.get("resource_access", {})
        client_roles = resource_access.get(settings.keycloak_client_id, {})
        roles = set(client_roles.get("roles", []))
        roles.update(payload.get("realm_access", {}).get("roles", []))
        if settings.admin_role not in roles:
            raise HTTPException(status_code=403, detail="Admin access required")
    else:
        if settings.admin_token:
            admin_token = request.headers.get("X-Admin-Token", "")
            if admin_token != settings.admin_token:
                raise HTTPException(status_code=403, detail="Invalid admin token")
