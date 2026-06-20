"""Base classes for authenticated actions that call external Keycloak-protected services.

Usage:
    from dac_web.actions import AuthenticatedActionBase

    class FetchFromTCBackend(AuthenticatedActionBase):
        CAPTION = "Fetch TC resource"

        def __call__(self, resource_id: str) -> DataNode:
            resp = self.auth_get(f"http://tc-backend:8000/api/nodes/{resource_id}")
            resp.raise_for_status()
            ...
"""

from contextlib import contextmanager

import httpx
from dac.core.actions import ProcessActionBase


class AuthenticatedActionBase(ProcessActionBase):
    """Action base that carries the user's Keycloak JWT token.

    Subclasses automatically receive the token injected as ``self._auth_token``
    before ``__call__`` is invoked. Use the helper methods ``auth_get``,
    ``auth_post``, ``auth_request`` or the ``auth_http_client`` context
    manager to include the bearer token in outbound HTTP requests.

    Set ``_REQUIRES_AUTH_TOKEN = False`` on a subclass to opt out.
    """

    _REQUIRES_AUTH_TOKEN = True

    @property
    def auth_token(self) -> str | None:
        """The user's Keycloak JWT token, or None when auth is disabled."""
        return getattr(self, '_auth_token', None)

    def _auth_headers(self) -> dict:
        if self.auth_token:
            return {"Authorization": f"Bearer {self.auth_token}"}
        return {}

    @contextmanager
    def auth_http_client(self, *, timeout: float | None = None):
        """Context manager yielding an ``httpx.Client`` with the bearer token pre-set.

        Usage::

            with self.auth_http_client() as client:
                r1 = client.get("http://other-service/api/a")
                r2 = client.get("http://other-service/api/b")
        """
        headers = self._auth_headers()
        with httpx.Client(headers=headers, timeout=timeout) as client:
            yield client

    def auth_request(self, method: str, url: str, **kwargs) -> httpx.Response:
        """Single HTTP request with the bearer token."""
        headers = kwargs.pop("headers", {})
        headers.update(self._auth_headers())
        with httpx.Client(timeout=kwargs.pop("timeout", None)) as client:
            return client.request(method, url, headers=headers, **kwargs)

    def auth_get(self, url: str, **kwargs) -> httpx.Response:
        """``GET`` request with the bearer token."""
        return self.auth_request("GET", url, **kwargs)

    def auth_post(self, url: str, **kwargs) -> httpx.Response:
        """``POST`` request with the bearer token."""
        return self.auth_request("POST", url, **kwargs)

    def auth_put(self, url: str, **kwargs) -> httpx.Response:
        """``PUT`` request with the bearer token."""
        return self.auth_request("PUT", url, **kwargs)

    def auth_delete(self, url: str, **kwargs) -> httpx.Response:
        """``DELETE`` request with the bearer token."""
        return self.auth_request("DELETE", url, **kwargs)
