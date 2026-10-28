"""Convert DAC data nodes and push them into a TC item.

The first supported shapes are ``TimeData`` and ``FreqDomainData``, both
mapped onto TC's ``Tabular.v00`` content type. The source application records
a contribution on TC so one item can collect results from several projects.
"""

from __future__ import annotations

import re
from typing import Any, Iterable, Optional

import numpy as np

from dac_web.config import settings

MAX_POINTS_PER_CHANNEL = 50_000
MAX_TOTAL_POINTS = 150_000
MAX_CHANNELS = 200


class TcPushError(RuntimeError):
    pass


def _channel_id(name: str, index: int) -> str:
    cleaned = re.sub(r"[^0-9A-Za-z_]+", "_", name or "").strip("_")
    return cleaned or f"channel_{index}"


def _downsample(
    x: np.ndarray, y: np.ndarray, max_points: int
) -> tuple[np.ndarray, np.ndarray]:
    if y.size <= max_points:
        return x, y
    indices = np.linspace(0, y.size - 1, max_points).astype(int)
    return x[indices], y[indices]


def _real_values(values: np.ndarray) -> np.ndarray:
    if np.iscomplexobj(values):
        return np.abs(values)
    return values


def _channel_payload(channel: Any, index: int, max_points: int) -> dict:
    name = getattr(channel, "name", None) or f"channel_{index}"
    y = _real_values(np.asarray(getattr(channel, "y", []))).astype(float)
    x = np.asarray(getattr(channel, "x", []), dtype=float)
    if x.size != y.size:
        x = np.arange(y.size, dtype=float)
    x, y = _downsample(x, y, max_points)
    channel_id = _channel_id(name, index)
    unit = getattr(channel, "y_unit", None) or "-"
    return {
        "name": name,
        "id_name": channel_id,
        "unit": unit,
        "data": [
            {
                "id_idx": channel_id,
                "time": float(xi),
                "value": float(yi),
            }
            for xi, yi in zip(x, y)
        ],
    }


def build_tabular_payload(channels: Iterable[Any]) -> dict:
    items = list(channels)
    if len(items) > MAX_CHANNELS:
        raise TcPushError(
            f"Too many channels ({len(items)}); maximum is {MAX_CHANNELS}"
        )
    budget = max(1, MAX_TOTAL_POINTS // len(items))
    per_channel = min(MAX_POINTS_PER_CHANNEL, budget)
    payload_channels = [
        _channel_payload(channel, index, per_channel)
        for index, channel in enumerate(items)
    ]
    if not payload_channels:
        raise TcPushError("No channels to push")
    return {"type": "Tabular.v00", "channels": payload_channels}


def _frozen(state: dict) -> bool:
    if "frozen" in state:
        return bool(state.get("frozen"))
    statuses = {
        item.strip()
        for item in settings.external_frozen_statuses.split(",")
        if item.strip()
    }
    return bool(state.get("status") in statuses)


def push_payload_to_tc(
    action: Any,
    *,
    target_node_id: str,
    source_id: str,
    payload: dict,
    mode: str = "a",
) -> dict:
    target_node_id = (target_node_id or "").strip()
    source_id = (source_id or "").strip()
    if not target_node_id:
        raise TcPushError("target_node_id is not configured")
    if not source_id or source_id == "new":
        raise TcPushError("Save the project before pushing results to TC")
    if mode not in {"a", "w"}:
        raise TcPushError("mode must be 'a' or 'w'")

    base = settings.external_system_url.rstrip("/")
    action.message(f"Checking TC item {target_node_id} ...")
    state_resp = action.auth_get(f"{base}/api/nodes/{target_node_id}/state")
    if state_resp.status_code == 404:
        raise TcPushError("TC item not found")
    if state_resp.status_code in (401, 403):
        raise TcPushError("TC rejected the request; check your login and permissions")
    if state_resp.status_code >= 400:
        raise TcPushError(f"TC state request failed ({state_resp.status_code})")
    state = state_resp.json()
    if _frozen(state):
        raise TcPushError(
            f"TC item is frozen (status '{state.get('status')}') and cannot be pushed"
        )

    source_url = f"{settings.public_base_url.rstrip('/')}/projects/{source_id}"
    channel_count = len(payload.get("channels") or [])
    action.message(f"Pushing {channel_count} channel(s) ...")
    resp = action.auth_put(
        f"{base}/api/nodes/{target_node_id}/push/data",
        json={
            "content": payload,
            "data_type": "Tabular.v00",
            "mode": mode,
            "source_system": "dac_web",
            "source_id": source_id,
            "source_part": "result",
            "source_url": source_url,
        },
    )
    if resp.status_code == 423:
        raise TcPushError("TC item is frozen and cannot be pushed")
    if resp.status_code in (401, 403):
        raise TcPushError("TC rejected the push; check your login and permissions")
    if resp.status_code >= 400:
        detail: Optional[str]
        try:
            detail = resp.json().get("detail")
        except ValueError:
            detail = resp.text
        raise TcPushError(f"TC push failed: {detail}")
    action.message("Push complete")
    return resp.json()
