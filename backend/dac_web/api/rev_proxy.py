"""Reverse proxy

Pass all "/app" requests to internal app services.
"""

import asyncio
import json
import logging

import httpx
import websockets
from fastapi import (
    APIRouter,
    Request,
    WebSocket,
    WebSocketDisconnect,
    HTTPException,
    Query,
)
from fastapi.responses import Response, StreamingResponse
from websockets.exceptions import ConnectionClosedError, ConnectionClosedOK

from dac_web.api.handler import user_manager, SESSID_KEY

logger = logging.getLogger(__name__)

router = APIRouter()



sse_client = httpx.AsyncClient(timeout=None)

@router.get("/{context_key_id}/actions/{action_id}/run")
async def proxy_sse_run_action(context_key_id: str, action_id: str, request: Request, sessid: str | None = Query(None, alias=SESSID_KEY)):
    uuid = sessid or request.headers.get(SESSID_KEY)
    if uuid is None or not user_manager.validate_sess(uuid):
        raise HTTPException(status_code=401, detail="Invalid or missing session ID")
    else:
        conn = user_manager.get_sess_conn(uuid)

    # include original query string when forwarding to internal host
    query = request.url.query
    if query:
        url = f"http://{conn}/{context_key_id}/actions/{action_id}/run?{query}"
    else:
        url = f"http://{conn}/{context_key_id}/actions/{action_id}/run"
    body = await request.body()

    # forward original headers but ensure session id header is present
    headers = dict(request.headers)
    headers[SESSID_KEY] = uuid

    async def generate_chunks():
        try:
            async with sse_client.stream("GET", url, content=body, headers=headers) as resp:
                async for chunk in resp.aiter_raw():
                    yield chunk
        except httpx.RequestError as e:
            logger.error("SSE proxy request failed: %s", e)
            yield f"event: error\ndata: {json.dumps({'message': str(e)})}\n\n"

    return StreamingResponse(
        generate_chunks(), 
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"}
    )



http_client = httpx.AsyncClient()

@router.api_route(
    "/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"]
)
async def proxy_http(
    request: Request, path: str, sessid: str | None = Query(None, alias=SESSID_KEY)
):
    uuid = sessid or request.headers.get(SESSID_KEY)
    if uuid is None or not user_manager.validate_sess(uuid):
        raise HTTPException(status_code=401, detail="Invalid or missing session ID")
    else:
        conn = user_manager.get_sess_conn(uuid)

    url = f"http://{conn}/{path}"
    body = await request.body()

    # forward original headers but ensure session id header is present
    headers = dict(request.headers)
    headers[SESSID_KEY] = uuid

    try:
        response = await http_client.request(
            method=request.method, url=url, headers=headers, content=body
        )
    except httpx.RequestError as e:
        logger.error("Proxy request failed: %s", e)
        raise HTTPException(status_code=502, detail=f"Upstream request failed: {e}")

    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers),
    )



@router.websocket("/{path:path}")
async def proxy_websocket(
    websocket: WebSocket, path: str, sessid: str | None = Query(None, alias=SESSID_KEY)
):
    await websocket.accept()
    uuid = sessid or websocket.headers.get(SESSID_KEY)

    if uuid is None or not user_manager.validate_sess(uuid):
        await websocket.close(code=3000, reason="Invalid or missing session ID")
        return
    conn = user_manager.get_sess_conn(uuid)

    internal_url = f"ws://{conn}/{path}"

    async with websockets.connect(internal_url) as internal_ws:

        async def client_to_target():
            try:
                while True:
                    message = await websocket.receive()
                    if "text" in message:
                        await internal_ws.send(message["text"])
                    elif "bytes" in message:
                        await internal_ws.send(message["bytes"])
            except RuntimeError:  # from `websocket`
                logger.debug("Client to target websocket closed")
            except (ConnectionClosedOK, ConnectionClosedError):  # from `internal_ws`
                logger.debug("Client to target connection closed")

        async def target_to_client():
            try:
                while True:
                    data = await internal_ws.recv()
                    if isinstance(data, str):
                        await websocket.send_text(data)
                    elif isinstance(data, bytes):
                        await websocket.send_bytes(data)
            except WebSocketDisconnect:  # from `websocket`
                logger.debug("Target to client websocket disconnected")
            except (ConnectionClosedOK, ConnectionClosedError):  # from `internal_ws`
                logger.debug("Target to client connection closed")

        await asyncio.gather(client_to_target(), target_to_client())
