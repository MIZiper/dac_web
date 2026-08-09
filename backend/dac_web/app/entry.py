import logging
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse
from uvicorn import Config, Server

from matplotlib.figure import Figure
import matplotlib.backends.backend_webagg_core as core
from matplotlib._pylab_helpers import Gcf

from dac_web.app.handler import FIG_NUM, router as dac_router
from dac_web.webagg_starlette import app as mpl_app
from dac_web.config import DEBUG
import dac_web.schema as s

logger = logging.getLogger(__name__)

app = FastAPI()


async def _http_exception_handler(request: Request, exc: Exception):
    import traceback
    status_code = getattr(exc, "status_code", 500)
    detail = str(exc.detail) if hasattr(exc, "detail") else str(exc)
    err = s.DACErrorResponse(code=status_code, message=detail, detail=None)
    if DEBUG:
        tb = traceback.format_exc()
        err.detail = s.DACErrorDetail(
            traceback=tb,
            endpoint=request.url.path,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
    logger.error("Subprocess error %d: %s", status_code, detail)
    return JSONResponse(status_code=status_code, content=err.model_dump())


async def _generic_exception_handler(request: Request, exc: Exception):
    import traceback
    err = s.DACErrorResponse(code=500, message="Internal server error", detail=None)
    if DEBUG:
        tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
        err.detail = s.DACErrorDetail(
            traceback=tb,
            endpoint=request.url.path,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
    logger.exception("Unhandled subprocess error on %s", request.url.path)
    return JSONResponse(status_code=500, content=err.model_dump())


app.add_exception_handler(HTTPException, _http_exception_handler)  # type: ignore[arg-type]
app.add_exception_handler(Exception, _generic_exception_handler)  # type: ignore[arg-type]

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
        # parent process reads this line from stdout to discover the port
        print(f"APP handler is running on port ... {port}", flush=True)

    async def shutdown(self, sockets=None):
        logger.info("Uvicorn is shutting down.")

        await super().shutdown(sockets)


def main():
    config = Config("dac_web.app.entry:app", host="localhost", port=0)
    server = CustomServer(config)
    server.run()


if __name__ == "__main__":
    main()
