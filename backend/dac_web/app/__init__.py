from fastapi import FastAPI

import matplotlib as mpl
from matplotlib.figure import Figure
import matplotlib.backends.backend_webagg_core as core
from matplotlib._pylab_helpers import Gcf

from dac_web.app.handler import FIG_NUM, app as dac_app
from dac_web.webagg_starlette import app as mpl_app

app = FastAPI()

figure = Figure(figsize=(10, 6))
manager: core.FigureManagerWebAgg = core.new_figure_manager_given_figure(num=FIG_NUM, figure=figure)
Gcf._set_new_active_manager(manager)

app.mount("/mpl", mpl_app)
app.mount("", dac_app)

def main():
    import uvicorn
    uvicorn.run("dac_web.app:app", host='localhost', port=0)


if __name__=="__main__":
    # print(f"[App] Listening on ... {host}:{port}", flush=True) # force flush, otherwise router may wait and block

    main()