"""WebAgg backend for Matplotlib using Starlette.

Adapted from "matplotlib.backends.backend_webagg.py".
It provides the handling by Starlette, and can be used in FastAPI or other ASGI frameworks.
"""

import json
import base64, asyncio
import mimetypes
from io import BytesIO
from pathlib import Path

from starlette.applications import Starlette
from starlette.responses import Response, FileResponse, HTMLResponse, PlainTextResponse
from starlette.routing import Route, WebSocketRoute, Mount
from starlette.staticfiles import StaticFiles
from starlette.websockets import WebSocket
from starlette.endpoints import WebSocketEndpoint

import matplotlib as mpl
from matplotlib._pylab_helpers import Gcf
from matplotlib.backends import backend_webagg_core as core

import nest_asyncio
nest_asyncio.apply()  # Allow nested event loops

STATIC_PATH = str(core.FigureManagerWebAgg.get_static_file_path())
IMAGES_PATH = str(Path(mpl.get_data_path(), 'images'))
FIG_NUM = 1

async def favicon(request):
    icon_path = Path(mpl.get_data_path(), 'images/matplotlib.png')
    return FileResponse(icon_path, media_type='image/png')

async def single_figure_page(request):
    ws_uri = f'ws://{request.headers["host"]}/'
    prefix=""

    html = f"""
<!DOCTYPE html>
<html lang="en">
  <head>
    <link rel="stylesheet" href="{ prefix }/_static/css/page.css" type="text/css">
    <link rel="stylesheet" href="{ prefix }/_static/css/boilerplate.css" type="text/css">
    <link rel="stylesheet" href="{ prefix }/_static/css/fbm.css" type="text/css">
    <link rel="stylesheet" href="{ prefix }/_static/css/mpl.css" type="text/css">
    <script src="{ prefix }/_static/js/mpl_tornado.js"></script>
    <script src="{ prefix }/js/mpl.js"></script>
    <script>
      function ready(fn) {{
        if (document.readyState != "loading") {{
          fn();
        }} else {{
          document.addEventListener("DOMContentLoaded", fn);
        }}
      }}

      ready(
        function () {{
          var websocket_type = mpl.get_websocket_type();
          var uri = "{ ws_uri }" + { FIG_NUM } + "/ws";
          if (window.location.protocol === 'https:') uri = uri.replace('ws:', 'wss:')
          var websocket = new websocket_type(uri);
          var fig = new mpl.figure(
              { FIG_NUM }, websocket, mpl_ondownload,
              document.getElementById("figure"));
        }}
      );
    </script>

    <title>matplotlib</title>
  </head>

  <body>
    <div id="mpl-warnings" class="mpl-warnings"></div>
    <div id="figure" style="margin: 10px 10px;"></div>
  </body>
</html>
    """
    
    return HTMLResponse(html)

async def mpl_js(request):
    js_content = core.FigureManagerWebAgg.get_javascript()
    return Response(js_content, media_type='application/javascript')

async def download(request):
    fignum = int(request.path_params['fignum'])
    fmt = request.path_params['fmt']
    manager = Gcf.get_fig_manager(fignum)
    buff = BytesIO()
    manager.canvas.figure.savefig(buff, format=fmt)
    content_type = mimetypes.types_map.get(f".{fmt}", 'application/octet-stream')
    return Response(buff.getvalue(), media_type=content_type)

class WebAggWSEndpoint(WebSocketEndpoint):
    supports_binary = True

    async def on_connect(self, websocket: WebSocket):
        self.websocket = websocket
        await websocket.accept()
        self.fignum = int(websocket.path_params['fignum'])
        self.manager = Gcf.get_fig_manager(self.fignum)
        self.manager.add_web_socket(self)

    async def on_disconnect(self, websocket: WebSocket, close_code: int):
        self.manager.remove_web_socket(self)

    async def on_receive(self, websocket: WebSocket, data: str):
        message = json.loads(data)
        if message['type'] == 'supports_binary':
            self.supports_binary = message['value']
        else:
            manager = Gcf.get_fig_manager(self.fignum)
            if manager is not None:
                manager.handle_json(message)

    def send_json(self, content):
        loop = asyncio.get_event_loop()
        coroutine = self.websocket.send_json(content)

        loop.run_until_complete(coroutine)

    def send_binary(self, blob):
        loop = asyncio.get_event_loop()
        if self.supports_binary:
            coroutine = self.websocket.send_bytes(blob)
        else:
            # Convert binary data to base64 string if binary is not supported
            coroutine = self.websocket.send_text(base64.b64encode(blob).decode('utf-8'))

        loop.run_until_complete(coroutine)

routes = [
    Route('/favicon.ico', favicon),
    Route('/', single_figure_page),
    Route('/js/mpl.js', mpl_js),
    Route('/{fignum:int}/download.{fmt}', download),
    WebSocketRoute('/{fignum:int}/ws', WebAggWSEndpoint),
    Mount('/_static', StaticFiles(directory=STATIC_PATH), name='static'),
    Mount('/_images', StaticFiles(directory=IMAGES_PATH), name='images'),
]

app = Starlette(debug=False, routes=routes)

"""
I don't like current implementation, there are some issues.

- It supports only one websocket connection.
  If with multiple connections, there will be error accumulation on the diff image.
  This should due to the force async to sync patch.
- With the nested event loop patch, error occurs when exiting.

Why tornado use async too, but no `async` required?
And why there is no official function to change async to sync?
When new websocket connection, new endpoint is created, then why pass websocket as parameter?
"""

if __name__ == '__main__':
    import uvicorn
    from matplotlib.figure import Figure
    

    FIG_NUM = 1
    figure = Figure(figsize=(10, 6))
    core.FigureManagerWebAgg._toolbar2_class = core.NavigationToolbar2WebAgg
    manager: core.FigureManagerWebAgg = core.new_figure_manager_given_figure(num=FIG_NUM, figure=figure)
    Gcf._set_new_active_manager(manager)

    ax = figure.add_subplot(111)
    ax.plot([0, 1, 2], [0, 1, 0.5], label='Sample Line')
    ax.set_title('Sample Plot')
    ax.legend()

    uvicorn.run(app)