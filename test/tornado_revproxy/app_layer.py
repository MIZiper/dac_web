import tornado.ioloop
import tornado.httpserver
import tornado.web
from tornado.netutil import bind_unix_socket, bind_sockets

import argparse, signal

from matplotlib.backends.backend_webagg import WebAggApplication, Gcf, FigureManagerWebAgg, new_figure_manager_given_figure
from matplotlib.figure import Figure

FIG_NUM = 1

application = WebAggApplication("/mpl")
figure = Figure(figsize=(10, 6))
manager: FigureManagerWebAgg = new_figure_manager_given_figure(num=FIG_NUM, figure=figure)
Gcf.set_active(manager)

if __name__=="__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-f', '--sock-file', type=str, required=False,
        help="Use Unix sock file"
    )
    parser.add_argument(
        '-p', '--port', type=int, default=5000,
        help="Port to listen on"
    )
    parser.add_argument(
        '-a', '--address', type=str, default='localhost',
        help="Address to listen on"
    )
    args = parser.parse_args()

    server = tornado.httpserver.HTTPServer(application)
    if args.sock_file:
        sockets = [bind_unix_socket(args.sock_file)]
    else:
        sockets = bind_sockets(args.port, '')
    server.add_sockets(sockets)
    for s in sockets:
        print(s)

    ioloop = tornado.ioloop.IOLoop.instance()
    ioloop.start()

    # tornado.ioloop.IOLoop.current().start()