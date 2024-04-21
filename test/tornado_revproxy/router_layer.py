from typing import Awaitable
import tornado
from tornado.httputil import HTTPServerRequest
from tornado.web import Application, RequestHandler, StaticFileHandler, FallbackHandler
from tornado.websocket import WebSocketClientConnection, WebSocketHandler, websocket_connect
from tornado.wsgi import WSGIContainer

from flask import Flask

app = Flask(__name__)

@app.route("/")
def index():
    return "Hello!"

tr = WSGIContainer(app)

class AppWebSocketHandler(WebSocketHandler):
    def __init__(self, application, request, **kwargs):
        super().__init__(application, request, **kwargs)

        self.connection = websocket_connect(
            ...,
            on_message_callback=self.write_message
        )

    def open(self, *args: str, **kwargs: str) -> Awaitable[None] | None:
        return super().open(*args, **kwargs)
    
    def on_message(self, message: str | bytes) -> Awaitable[None] | None:
        return super().on_message(message)
    
    def on_close(self) -> None:
        return super().on_close()
    
class AppHTTPHandler(tornado.web.RequestHandler):
    async def prepare(self):
        # Prepare the proxy request
        target_url = "http://backend-server:8080"  # Replace with your backend server URL
        self.proxy_request = tornado.httpclient.HTTPRequest(
            url=target_url + self.request.uri,
            method=self.request.method,
            body=self.request.body,
            headers=self.request.headers,
            follow_redirects=False,
            allow_nonstandard_methods=True,
        )

    async def forward_request(self):
        try:
            response = await tornado.httpclient.AsyncHTTPClient().fetch(self.proxy_request)
            self.set_status(response.code)
            for header, value in response.headers.get_all():
                self.set_header(header, value)
            self.write(response.body)
        except tornado.httpclient.HTTPError as e:
            self.set_status(e.code)
            self.write(f"Error: {e.code} {e.message}")

    async def get(self):
        await self.forward_request()
    async def post(self):
        await self.forward_request()
    async def put(self):
        await self.forward_request()
    async def delete(self):
        await self.forward_request()
    async def patch(self):
        await self.forward_request()
    async def options(self):
        await self.forward_request()
    async def head(self):
        await self.forward_request()

application = Application([
    (r"/app/(.*)/ws", AppWebSocketHandler),
    (r"/app/(.*)", AppHTTPHandler),
    (r".*", FallbackHandler, dict(fallback=tr)),
])

if __name__=="__main__":
    server = tornado.httpserver.HTTPServer(application)
    sockets = tornado.netutil.bind_sockets(5000)
    server.add_sockets(sockets)

    tornado.ioloop.IOLoop.current().start()