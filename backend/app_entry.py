from pathlib import Path
import argparse

import tornado
from tornado.wsgi import WSGIContainer
from tornado.web import FallbackHandler

import matplotlib as mpl
from matplotlib.figure import Figure
from matplotlib.backends.backend_webagg import WebAggApplication, new_figure_manager_given_figure, FigureManagerWebAgg, Gcf
import matplotlib.backends.backend_webagg_core as core

from app_handler import app, FIG_NUM



mpl_prefix = "/mpl"
tr = WSGIContainer(app)

class MyApplication(WebAggApplication):
    # Copy from `WebAggApplication`, only to insert handler

    class WebSocket(WebAggApplication.WebSocket):
        def check_origin(self, origin: str) -> bool:
            return True
        
    def __init__(self, url_prefix=''):
        if url_prefix:
            assert url_prefix[0] == '/' and url_prefix[-1] != '/', \
                'url_prefix must start with a "/" and not end with one.'

        tornado.web.Application.__init__(
            self,
            [
                # Static files for the CSS and JS
                (url_prefix + r'/_static/(.*)',
                 tornado.web.StaticFileHandler,
                 {'path': core.FigureManagerWebAgg.get_static_file_path()}),

                # Static images for the toolbar
                (url_prefix + r'/_images/(.*)',
                 tornado.web.StaticFileHandler,
                 {'path': Path(mpl.get_data_path(), 'images')}),

                # A Matplotlib favicon
                (url_prefix + r'/favicon.ico', self.FavIcon),

                # The page that contains all of the pieces
                (url_prefix + r'/([0-9]+)', self.SingleFigurePage,
                 {'url_prefix': url_prefix}),

                # The page that contains all of the figures
                (url_prefix + r'/?', self.AllFiguresPage,
                 {'url_prefix': url_prefix}),

                (url_prefix + r'/js/mpl.js', self.MplJs),

                # Sends images and events to the browser, and receives
                # events from the browser
                (url_prefix + r'/([0-9]+)/ws', self.WebSocket),

                # Handles the downloading (i.e., saving) of static images
                (url_prefix + r'/([0-9]+)/download.([a-z0-9.]+)',
                 self.Download),
                 
                (r".*", FallbackHandler, dict(fallback=tr))
            ],
            template_path=core.FigureManagerWebAgg.get_static_file_path()
        )

application = MyApplication(url_prefix=mpl_prefix)
figure = Figure(figsize=(10, 6))
manager: FigureManagerWebAgg = new_figure_manager_given_figure(num=FIG_NUM, figure=figure)
Gcf._set_new_active_manager(manager)

if __name__=="__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-p', '--port', type=int, default=5000,
        help="Port to listen on"
    )
    parser.add_argument(
        '--host', type=str, default='localhost',
        help="Host to listen on"
    )
    args = parser.parse_args()
    
    server = tornado.httpserver.HTTPServer(application)
    sockets = tornado.netutil.bind_sockets(args.port, args.host)
    server.add_sockets(sockets)
    for s in sockets:
        host, port = s.getsockname()
        print(f"[App] Listening on ... {host}:{port}", flush=True) # force flush, otherwise router may wait and block

    ioloop = tornado.ioloop.IOLoop.current()
    ioloop.add_callback(lambda: print(">> Ready <<"))
    ioloop.start()