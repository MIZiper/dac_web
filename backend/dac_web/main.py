import os

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from dac_web.router.rev_proxy import app as proxy_app
from dac_web.router.handler import app as handler_app

app = FastAPI()

app.mount("/api", handler_app)
app.mount("/app", proxy_app)

FRONTEND_DIST = os.getenv("FRONTEND_DIST")
if FRONTEND_DIST is not None and os.path.isdir(FRONTEND_DIST):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIST), name="static")

    @app.get("/")
    def serve_index():
        return FileResponse(os.path.join(FRONTEND_DIST, "index.html"))

    @app.get("/{full_path:path}")
    def serve_spa(full_path: str):
        file_path = os.path.join(FRONTEND_DIST, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(FRONTEND_DIST, "index.html"))


def main():
    import uvicorn

    uvicorn.run("dac_web.main:app", host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
