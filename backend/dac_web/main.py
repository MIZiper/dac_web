import os

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from dac_web.router.rev_proxy import router as rev_router
from dac_web.router.handler import router as api_router
from dac_web.app.handler import router as app_doc_router

app = FastAPI()

app.include_router(api_router, prefix="/api", tags=["API"])
app.include_router(rev_router, prefix="/app", include_in_schema=False)
app.include_router(app_doc_router, prefix="/app", tags=["APP"]) # for /docs purpose only, and seems the /app routing is overshadowed by rev_router

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
