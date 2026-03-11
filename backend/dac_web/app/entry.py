from fastapi import FastAPI, APIRouter
import os, sys
from datetime import datetime
from uvicorn import Config, Server

from matplotlib.figure import Figure
import matplotlib.backends.backend_webagg_core as core
from matplotlib._pylab_helpers import Gcf

from dac_web.app.handler import FIG_NUM, router as dac_router
from dac_web.webagg_starlette import app as mpl_app

app = FastAPI()

figure = Figure(figsize=(10, 6))
core.FigureManagerWebAgg._toolbar2_class = core.NavigationToolbar2WebAgg
manager: core.FigureManagerWebAgg = core.new_figure_manager_given_figure(
    num=FIG_NUM, figure=figure
)
Gcf._set_new_active_manager(manager)

app.mount("/mpl", mpl_app)
app.include_router(dac_router, prefix="")



class CustomServer(Server):
    async def startup(self, sockets=None):
        await super().startup(sockets)
        # Get the actual port from the bound socket
        port = self.servers[0].sockets[0].getsockname()[1]
        print(f"✅ APP handler is running on port ... {port}", flush=True)

    async def shutdown(self, sockets=None):
        print("🛑 Uvicorn is shutting down.", flush=True)

        await super().shutdown(sockets)


def main():
    config = Config("dac_web.app.entry:app", host="localhost", port=0)
    server = CustomServer(config)
    server.run()


if __name__ == "__main__":
    main()
