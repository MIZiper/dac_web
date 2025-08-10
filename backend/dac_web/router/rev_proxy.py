"""Reverse proxy

Pass all "/app" requests to internal app services.
"""

import asyncio
import websockets
import httpx
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import Response

from dac_web.router.handler import user_manager, SESSID_KEY

app = FastAPI()

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def proxy_http(request: Request, path: str):
    # self.set_header('Access-Control-Allow-Methods', 'GET, PUT, POST, DELETE, OPTIONS')
    # self.set_header("Access-Control-Allow-Headers", "access-control-allow-origin,authorization,content-type,x-requested-with")
    # self.add_header("Access-Control-Allow-Headers", SESSID_KEY)

    async with httpx.AsyncClient() as client:
        uuid = request.headers.get(SESSID_KEY) or request.url.get_query_argument(SESSID_KEY)
        if not user_manager.validate_sess(uuid):
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
async def proxy_websocket(websocket: WebSocket, path: str):
    uuid = websocket.headers.get(SESSID_KEY) or websocket.get_query_argument(SESSID_KEY)

    if not user_manager.validate_sess(uuid):
        await websocket.send_denial_response()
        return
    conn = user_manager.get_sess_conn(uuid)

    await websocket.accept()
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
            except WebSocketDisconnect:
                await internal_ws.close()
            except Exception:
                await internal_ws.close()

        async def target_to_client():
            try:
                while True:
                    data = await internal_ws.recv()
                    if isinstance(data, str):
                        await websocket.send_text(data)
                    elif isinstance(data, bytes):
                        await websocket.send_bytes(data)
            except Exception:
                await websocket.close()

        await asyncio.gather(client_to_target(), target_to_client())