"""Reverse proxy

Pass all "/app" requests to internal app services.
"""

import asyncio
import websockets
from websockets.exceptions import ConnectionClosedError, ConnectionClosedOK
import httpx
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, HTTPException, Query
from fastapi.responses import Response

from dac_web.router.handler import user_manager, SESSID_KEY

app = FastAPI()

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def proxy_http(request: Request, path: str, sessid: str | None = Query(None, alias=SESSID_KEY)):
    async with httpx.AsyncClient() as client: # TODO: try to reuse the client, otherwise every http request is a new connection to internal service
        uuid = sessid or request.headers.get(SESSID_KEY)
        if uuid is None or not user_manager.validate_sess(uuid):
            raise HTTPException(status_code=401, detail="Invalid or missing session ID")
        else:
            conn = user_manager.get_sess_conn(uuid)
            
        url = f"http://{conn}/{path}"
        headers = dict(request.headers)
        body = await request.body()

        response = await client.request(
            method=request.method,
            url=url,
            headers=headers,
            content=body
        )

        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=dict(response.headers)
        )

@app.websocket("/{path:path}")
async def proxy_websocket(websocket: WebSocket, path: str, sessid: str | None = Query(None, alias=SESSID_KEY)):
    await websocket.accept()
    uuid = sessid or websocket.headers.get(SESSID_KEY)

    if uuid is None or not user_manager.validate_sess(uuid):
        await websocket.close(code=3000, reason="Invalid or missing session ID")
        return
    conn = user_manager.get_sess_conn(uuid)

    internal_url = f"ws://{conn}/{path}"

    # TODO: there is an error since uvicorn==0.36, the websocket automatically got closed after established.
    # currently fix uvicorn==0.35
    async with websockets.connect(internal_url) as internal_ws:
        async def client_to_target():
            try:
                while True:
                    message = await websocket.receive()
                    if "text" in message:
                        await internal_ws.send(message["text"])
                    elif "bytes" in message:
                        await internal_ws.send(message["bytes"])
            except RuntimeError: # from `websocket`
                print("Client to target, RuntimeError")
            except (ConnectionClosedOK, ConnectionClosedError): # from `internal_ws`
                print("Client to target, ConnectionClosed")

        async def target_to_client():
            try:
                while True:
                    data = await internal_ws.recv()
                    if isinstance(data, str):
                        await websocket.send_text(data)
                    elif isinstance(data, bytes):
                        await websocket.send_bytes(data)
            except WebSocketDisconnect: # from `websocket`
                print("Target to client, WebSocketDisconnect")
            except (ConnectionClosedOK, ConnectionClosedError): # from `internal_ws`
                print("Target to client, ConnectionClosed")

        await asyncio.gather(client_to_target(), target_to_client())