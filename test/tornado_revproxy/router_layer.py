from typing import Awaitable
import tornado
from tornado.httputil import HTTPServerRequest
from tornado.web import Application, RequestHandler, StaticFileHandler, FallbackHandler
from tornado.websocket import WebSocketClientConnection, WebSocketHandler, websocket_connect
from tornado.wsgi import WSGIContainer

from flask import Flask, make_response
from uuid import uuid4
from os import path

import subprocess, socket

app = Flask(__name__)

containers = {}
SESSID = "dac-sess_id"

@app.route("/")
def index():
    return "Hello!"

@app.route("/new")
def new():
    uuid = uuid4().hex
    response = make_response(f"Set cookie: {uuid}")
    response.set_cookie(SESSID, uuid)

    print(f"[Flask/new] Started container {uuid}")

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('localhost', 0))
    host, port = s.getsockname()

    p_inst = subprocess.Popen(
        ["python", path.join(path.dirname(__file__), "app_layer.py"),
         "-p", f"{port}", "--host", host],
        # stdout=subprocess.PIPE,
        # stderr=subprocess.PIPE,
    )
    containers[uuid] = (f"{host}:{port}", p_inst,)

    return response

@app.route("/<path:path>")
def fallback(path):
    return f"Handle by Flask: {path}"

tr = WSGIContainer(app)

class AppWebSocketHandler(WebSocketHandler):
    async def open(self, *args: str, **kwargs: str) -> Awaitable[None] | None:
        print(f"[WS/open] Handle {args}, {kwargs}")
        uuid = self.get_cookie(SESSID)
        self.backend_ws = None

        if uuid not in containers:
            self.write_message("Container not found")
            self.close()
            return
        conn, p_inst = containers[uuid]

        print(f"[WS/open] Connected to {conn}")

        target_url = f"ws://{conn}"
        self.backend_ws = await websocket_connect(
            target_url + self.request.uri,
            on_message_callback=self._write_message
        )

    def _write_message(self, message: str | bytes | None):
        if message is None:
            return
        self.write_message(message, binary=isinstance(message, bytes))
    
    def on_message(self, message: str | bytes) -> Awaitable[None] | None:
        self.backend_ws.write_message(message)
    
    def on_close(self) -> None:
        if self.backend_ws is None:
            return
        self.backend_ws.close()
    
class AppHTTPHandler(tornado.web.RequestHandler):
    async def forward_request(self):
        try:
            uuid = self.get_cookie(SESSID)
            if uuid not in containers:
                self.set_status(404)
                self.write("Container not found")
                return
            else:
                conn, p_inst = containers[uuid]

            print(f"[HTTP/forward] Connected to {conn}")
            
            target_url = f"http://{conn}"
            proxy_request = tornado.httpclient.HTTPRequest(
                url=target_url + self.request.uri,
                method=self.request.method,
                body=self.request.body,
                headers=self.request.headers,
                follow_redirects=False,
                allow_nonstandard_methods=True,
            )
            
            print(f"[HTTP/before]")
            response = await tornado.httpclient.AsyncHTTPClient().fetch(proxy_request)
            print(f"[HTTP/after]")
            if response.code in (204, 304) or (100 <= response.code < 200):
                return
            self.set_status(response.code)
            for header, value in response.headers.get_all():
                self.set_header(header, value)
            self.write(response.body)
        except tornado.httpclient.HTTPError as e:
            print("Errrrrrrrrrrrrrrrrrrrrror")
            self.set_status(e.code)
            print(f"Error: {e.code} {e.message}")

    async def get(self, *args: str, **kwargs: str):
        print(f"[HTTP/get] Handle {args}, {kwargs}")
        await self.forward_request()
    async def post(self, *args: str, **kwargs: str):
        await self.forward_request()
    async def put(self, *args: str, **kwargs: str):
        await self.forward_request()
    async def delete(self, *args: str, **kwargs: str):
        await self.forward_request()
    async def patch(self, *args: str, **kwargs: str):
        await self.forward_request()
    async def options(self, *args: str, **kwargs: str):
        await self.forward_request()
    async def head(self, *args: str, **kwargs: str):
        await self.forward_request()

application = Application([
    (r"/app/(.*)/ws", AppWebSocketHandler),
    (r"/app/(.*)(?<!\/ws)", AppHTTPHandler),
    (r".*", FallbackHandler, dict(fallback=tr)),
])

if __name__=="__main__":
    server = tornado.httpserver.HTTPServer(application)
    sockets = tornado.netutil.bind_sockets(5000)
    server.add_sockets(sockets)
    for s in sockets:
        print(f"[Router] Listening on {s.getsockname()}")

    tornado.ioloop.IOLoop.current().start()