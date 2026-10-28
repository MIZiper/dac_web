"""Client for the external catalog/process system (TC in this release)."""

from __future__ import annotations

from typing import Any, Optional

import httpx

from dac_web.config import settings


class ExternalError(Exception):
    def __init__(self, status_code: int, detail: str):
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


def _base_url() -> str:
    return settings.external_system_url.rstrip("/")


def _headers(token: Optional[str]) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"} if token else {}


def _ensure_supported() -> None:
    if settings.external_system != "tc":
        raise ExternalError(501, f"Unsupported external system: {settings.external_system}")


async def _request(
    method: str,
    path: str,
    token: Optional[str],
    **kwargs: Any,
) -> Any:
    _ensure_supported()
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.request(
                method, f"{_base_url()}{path}", headers=_headers(token), **kwargs
            )
    except httpx.HTTPError as exc:
        raise ExternalError(503, f"External system unavailable: {exc}") from exc

    if resp.status_code == 404:
        raise ExternalError(404, "External resource not found")
    if resp.status_code in (401, 403):
        raise ExternalError(resp.status_code, "External system rejected the request")
    if resp.status_code >= 400:
        try:
            detail = resp.json().get("detail", resp.text)
        except ValueError:
            detail = resp.text
        raise ExternalError(502, f"External system error: {detail}")
    if resp.status_code == 204:
        return None
    return resp.json()


def frozen_statuses() -> set[str]:
    return {
        item.strip()
        for item in settings.external_frozen_statuses.split(",")
        if item.strip()
    }


def is_frozen(status: str | None) -> bool:
    return bool(status and status in frozen_statuses())


def external_url(external_id: str) -> str:
    return f"{settings.external_system_ui_url.rstrip('/')}/items/{external_id}"


def source_url(project_id: str) -> str:
    return f"{settings.public_base_url.rstrip('/')}/projects/{project_id}"


async def get_state(token: Optional[str], external_id: str) -> dict:
    return await _request("GET", f"/api/nodes/{external_id}/state", token)


async def attach_source(
    token: Optional[str],
    external_id: str,
    project_id: str,
) -> dict:
    return await _request(
        "PUT",
        f"/api/nodes/{external_id}/source",
        token,
        json={
            "source_system": "dac_web",
            "source_id": project_id,
            "source_part": "project",
            "source_url": source_url(project_id),
            "data_type": "dac_web.project",
        },
    )


async def detach_source(token: Optional[str], external_id: str) -> dict:
    return await _request("DELETE", f"/api/nodes/{external_id}/source", token)


async def query_candidates(
    token: Optional[str],
    text: str = "",
    page_size: int = 20,
) -> list[dict]:
    data = await _request(
        "GET",
        "/api/nodes/source-candidates",
        token,
        params={
            "source_system": "dac_web",
            "q": text or "",
            "page_size": page_size,
        },
    )
    return data.get("items", []) if isinstance(data, dict) else []


async def query_push_candidates(
    token: Optional[str],
    text: str = "",
    page_size: int = 20,
) -> list[dict]:
    data = await _request(
        "GET",
        "/api/nodes/push-candidates",
        token,
        params={
            "q": text or "",
            "page_size": page_size,
            "data_type": "Tabular.v00",
        },
    )
    return data.get("items", []) if isinstance(data, dict) else []


def result_source_url(project_id: str) -> str:
    return f"{settings.public_base_url.rstrip('/')}/projects/{project_id}"


async def push_data(
    token: Optional[str],
    external_id: str,
    content: dict,
    project_id: str,
    *,
    data_type: str = "Tabular.v00",
    mode: str = "a",
) -> dict:
    return await _request(
        "PUT",
        f"/api/nodes/{external_id}/push/data",
        token,
        json={
            "content": content,
            "data_type": data_type,
            "mode": mode,
            "source_system": "dac_web",
            "source_id": project_id,
            "source_part": "result",
            "source_url": result_source_url(project_id),
        },
    )


async def list_contributions(token: Optional[str], project_id: str) -> list[dict]:
    return await _request(
        "GET",
        "/api/nodes/contributions",
        token,
        params={"source_system": "dac_web", "source_id": project_id},
    )
