from fastapi import FastAPI
import os, sys
from datetime import datetime
from uvicorn import Config, Server

from matplotlib.figure import Figure
import matplotlib.backends.backend_webagg_core as core
from matplotlib._pylab_helpers import Gcf

from dac_web.app.handler import FIG_NUM, app as dac_app
from dac_web.webagg_starlette import app as mpl_app

app = FastAPI()

figure = Figure(figsize=(10, 6))
core.FigureManagerWebAgg._toolbar2_class = core.NavigationToolbar2WebAgg
manager: core.FigureManagerWebAgg = core.new_figure_manager_given_figure(
    num=FIG_NUM, figure=figure
)
Gcf._set_new_active_manager(manager)

app.mount("/mpl", mpl_app)
app.mount("", dac_app)

# log_fp = None
# orig_out = sys.stdout
# orig_err = sys.stderr


class CustomServer(Server):
    async def startup(self, sockets=None):
        await super().startup(sockets)
        # Get the actual port from the bound socket
        port = self.servers[0].sockets[0].getsockname()[1]
        print(f"✅ APP handler is running on port ... {port}", flush=True)

        # if log_fp is not None:
        #     sys.stdout = log_fp
        #     sys.stderr = log_fp

    async def shutdown(self, sockets=None):
        print("🛑 Uvicorn is shutting down.", flush=True)
        # if log_fp is not None:
        #     sys.stdout = orig_err
        #     sys.stderr = orig_err
        #     if not log_fp.closed:
        #         log_fp.close()
        await super().shutdown(sockets)


def main():
    # sess_id = os.getenv("APP_SESSID", "DEBUG")
    # logdir = os.getenv("LOG_DIR", "./storage/logs")
    # dolog = os.getenv("APP_LOG_ON")=="1"

    # if dolog:
    #     global log_fp
    #     log_fp = open(os.path.join(logdir, f"{datetime.now().strftime('%Y%m%d%H%M%S')}-{sess_id}.log"), mode="a")

    config = Config("dac_web.app:app", host="localhost", port=0)
    server = CustomServer(config)
    server.run()


if __name__ == "__main__":
    main()
