from fastapi import FastAPI
import os, sys
from datetime import datetime

from matplotlib.figure import Figure
import matplotlib.backends.backend_webagg_core as core
from matplotlib._pylab_helpers import Gcf

from dac_web.app.handler import FIG_NUM, app as dac_app
from dac_web.webagg_starlette import app as mpl_app

app = FastAPI()

figure = Figure(figsize=(10, 6))
core.FigureManagerWebAgg._toolbar2_class = core.NavigationToolbar2WebAgg
manager: core.FigureManagerWebAgg = core.new_figure_manager_given_figure(num=FIG_NUM, figure=figure)
Gcf._set_new_active_manager(manager)

app.mount("/mpl", mpl_app)
app.mount("", dac_app)

def main():
    import uvicorn

    port = int(os.getenv("APP_PORT", 0))
    sess_id = os.getenv("APP_SESSID")
    logdir = os.getenv("LOG_DIR", "./logs")

    if sess_id:
        with open(os.path.join(logdir, f"{datetime.now().strftime('%Y%m%d%H%M%S')}-{sess_id}.log"), mode="a") as fp:
            sys.stdout = fp
            sys.stderr = fp
            uvicorn.run("dac_web.app:app", host='localhost', port=port)
    else:
        uvicorn.run("dac_web.app:app", host='localhost', port=port)

if __name__=="__main__":
    main()