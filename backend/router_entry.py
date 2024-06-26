"""Router entry

Pass the request to backend app.
"""

import sys
from typing import Awaitable, Callable

import tornado
from tornado.httputil import HTTPServerRequest
from tornado.web import Application, RequestHandler, FallbackHandler
from tornado.websocket import WebSocketClientConnection, WebSocketHandler, websocket_connect
from tornado.wsgi import WSGIContainer

from router_handler import SESSID_KEY, app, user_manager, PROJDIR_KEY, SAVEDIR_KEY



site_prefix = "" # "/dac" #
app_prefix = "/app"
_N = len(site_prefix) + len(app_prefix)
tr = WSGIContainer(app)

class AppWebSocketHandler(WebSocketHandler):
    def check_origin(self, origin: str) -> bool:
        return True
    
    async def open(self, *args: str, **kwargs: str) -> Awaitable[None] | None:
        uuid = self.request.headers.get(SESSID_KEY) or self.get_query_argument(SESSID_KEY)
        self.backend_ws = None

        if not user_manager.validate_sess(uuid):
            self.write_message("Session not found, connection close")
            self.close()
            return
        conn = user_manager.get_sess_conn(uuid)

        self.backend_ws = await websocket_connect(
            url=f"ws://{conn}{self.request.uri[_N:]}", # remove "/app"
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
    
class AppHTTPHandler(RequestHandler):
    def set_default_headers(self) -> None:
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header('Access-Control-Allow-Methods', 'GET, PUT, POST, DELETE, OPTIONS')
        
        self.set_header("Access-Control-Allow-Headers", "access-control-allow-origin,authorization,content-type,x-requested-with")
        self.add_header("Access-Control-Allow-Headers", SESSID_KEY)

    async def forward_request(self):
        try:
            uuid = self.request.headers.get(SESSID_KEY) or self.get_query_argument(SESSID_KEY)
            if not user_manager.validate_sess(uuid):
                self.set_status(401)
                self.write("Session not found, unauth")
                return
            else:
                conn = user_manager.get_sess_conn(uuid)
            
            proxy_request = tornado.httpclient.HTTPRequest(
                url=f"http://{conn}{self.request.uri[_N:]}", # remove "/app"
                method=self.request.method,
                body=self.request.body,
                headers=self.request.headers,
                follow_redirects=False,
                allow_nonstandard_methods=True,
            )
            
            response = await tornado.httpclient.AsyncHTTPClient().fetch(proxy_request)
            if response.code in (204, 304) or (100 <= response.code < 200):
                return
            self.set_status(response.code)
            for header, value in response.headers.get_all():
                self.set_header(header, value)
            self.write(response.body)
        except tornado.httpclient.HTTPError as e:
            print(f"[Router/AppHTTP] Error: {e.code} {e.message}", file=sys.stderr)
            self.set_status(e.code)

    async def get(self, *args: str, **kwargs: str):
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
        self.set_status(204)
        self.finish()
    
    async def head(self, *args: str, **kwargs: str):
        await self.forward_request()

class AppFallbackHandler(FallbackHandler):
    def initialize(self, fallback: Callable[[HTTPServerRequest], None], prefix: str) -> None:
        self._prefix = prefix
        return super().initialize(fallback)
    
    def prepare(self) -> None:
        n = len(self._prefix)
        self.request.path = self.request.path[n:]
        self.request.uri = self.request.uri[n:]
        return super().prepare()

application = Application([
    (rf"{site_prefix}{app_prefix}/(.*)/ws", AppWebSocketHandler),
    (rf"{site_prefix}{app_prefix}/(.*)(?<!\/ws)", AppHTTPHandler),
    (rf"{site_prefix}.*", AppFallbackHandler, dict(fallback=tr, prefix=site_prefix)),
])

if __name__=="__main__":
    import argparse
    from os import path

    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--project-folder", type=str, default=path.join(path.dirname(__file__), "../projects"))
    parser.add_argument("--save-folder", type=str, default=path.join(path.dirname(__file__), "../projects_save"))
    args = parser.parse_args()
    app.config[PROJDIR_KEY] = args.project_folder
    app.config[SAVEDIR_KEY] = args.save_folder

    server = tornado.httpserver.HTTPServer(application)
    sockets = tornado.netutil.bind_sockets(port=args.port)
    server.add_sockets(sockets)
    for s in sockets:
        print(f"[Router] Listening on {s.getsockname()}")

    tornado.ioloop.IOLoop.current().start()