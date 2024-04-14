from flask import Blueprint, send_from_directory, Response
from flask_socketio.namespace import Namespace
from flask_socketio import emit
from os import path as os_path
import json

from matplotlib.figure import Figure
import matplotlib as mpl

from matplotlib.backends.backend_webagg_core import FigureManagerWebAgg, FigureCanvasWebAggCore

mpl_bp = Blueprint('mpl', __name__)

@mpl_bp.route('/_static/<path:path>')
def static(path):
    return send_from_directory(FigureManagerWebAgg.get_static_file_path(), path)

@mpl_bp.route('/_images/<path:path>')
def images(path):
    return send_from_directory(os_path.join(mpl.get_data_path(), 'images'), path)

@mpl_bp.route('/mpl.js')
def mpl_js():
    js_content = FigureManagerWebAgg.get_javascript()
    return Response(js_content, mimetype='application/javascript')

# @mpl_bp.route('/download.([a-z0-9.]+)')

class MplWebSocket(Namespace):
    supports_binary = True

    def __init__(self, namespace: str, manager: FigureManagerWebAgg) -> None:
        super().__init__(namespace)
        self.manager = manager
        self.canvas = canvas = manager.canvas
        self.figure = canvas.figure

    def on_connect(self):
        self.manager.add_web_socket(self)
        if hasattr(self, 'set_nodelay'):
            self.set_nodelay(True)

    def on_disconnect(self):
        self.manager.remove_web_socket(self)

    def on_message(self, message):
        message = json.loads(message)
        if message['type'] == 'supports_binary':
            self.supports_binary = message['value']
        else:
            self.manager.handle_json(message)

    def send_json(self, content):
        self.send(content)

    def send_binary(self, blob):
        if self.supports_binary:
            self.send(blob, binary=True)
        else:
            data_uri = "data:image/png;base64,{}".format(
                blob.encode('base64').replace('\n', '')
            )
            self.send(data_uri)