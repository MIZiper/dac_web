from pathlib import Path
import argparse

import matplotlib as mpl
from matplotlib.figure import Figure
from matplotlib.backends.backend_webagg import WebAggApplication, new_figure_manager_given_figure, FigureManagerWebAgg, Gcf
import matplotlib.backends.backend_webagg_core as core

from app_handler import app, FIG_NUM

from dac_web.webagg_starlette import app as mpl_app


mpl_prefix = "/mpl"

figure = Figure(figsize=(10, 6))
manager: FigureManagerWebAgg = new_figure_manager_given_figure(num=FIG_NUM, figure=figure)
Gcf._set_new_active_manager(manager)

def main():
    import uvicorn
    uvicorn.run("dac_web.app:app")


if __name__=="__main__":
    
    server = tornado.httpserver.HTTPServer(application)
    sockets = tornado.netutil.bind_sockets(args.port, args.host)
    server.add_sockets(sockets)
    for s in sockets:
        host, port = s.getsockname()
        print(f"[App] Listening on ... {host}:{port}", flush=True) # force flush, otherwise router may wait and block

    ioloop = tornado.ioloop.IOLoop.current()
    ioloop.add_callback(lambda: print(">> Ready <<"))
    ioloop.start()