"""Reverse proxy

Pass all "/app" requests to internal app services.
"""

import asyncio
import websockets
from websockets.exceptions import ConnectionClosedError, ConnectionClosedOK
import httpx
from fastapi import (
    FastAPI,
    APIRouter,
    Request,
    WebSocket,
    WebSocketDisconnect,
    HTTPException,
    Query,
)
from fastapi.responses import Response, StreamingResponse

from dac_web.api.handler import user_manager, SESSID_KEY

router = APIRouter()



sse_client = httpx.AsyncClient(timeout=None)

@router.post("/{context_key_id}/actions/{action_id}")
async def proxy_sse_run_action(context_key_id: str, action_id: str, request: Request):
    uuid = request.headers.get(SESSID_KEY)
    if uuid is None or not user_manager.validate_sess(uuid):
        raise HTTPException(status_code=401, detail="Invalid or missing session ID")
    else:
        conn = user_manager.get_sess_conn(uuid)

    url = f"http://{conn}/{context_key_id}/actions/{action_id}"
    body = await request.body()

    async def generate_chunks():
        async with sse_client.stream("POST", url, content=body, headers=request.headers.raw) as resp:
            async for chunk in resp.aiter_raw():
                yield chunk

    return StreamingResponse(
        generate_chunks(), 
        media_type="text/event-stream",
        headers={"X-Accel-Buffering": "no"} # 禁用 Nginx 缓冲
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

    response = await http_client.request(
        method=request.method, url=url, headers=request.headers.raw, content=body
    )

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
                print("Client to target, RuntimeError")
            except (ConnectionClosedOK, ConnectionClosedError):  # from `internal_ws`
                print("Client to target, ConnectionClosed")

        async def target_to_client():
            try:
                while True:
                    data = await internal_ws.recv()
                    if isinstance(data, str):
                        await websocket.send_text(data)
                    elif isinstance(data, bytes):
                        await websocket.send_bytes(data)
            except WebSocketDisconnect:  # from `websocket`
                print("Target to client, WebSocketDisconnect")
            except (ConnectionClosedOK, ConnectionClosedError):  # from `internal_ws`
                print("Target to client, ConnectionClosed")

        await asyncio.gather(client_to_target(), target_to_client())
