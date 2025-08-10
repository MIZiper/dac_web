from fastapi import FastAPI
from dac_web.router.rev_proxy import app as proxy_app
from dac_web.router.handler import app as handler_app

app = FastAPI()

app.mount("/api", handler_app)
app.mount("/app", proxy_app)

FRONTEND_DIST = os.getenv
if FRONTEND_DIST:
    @app.get("/")
    def serve_index():
        pass

    @app.get("/{full_path:path}")
    def serve_spa(full_path: str):
        pass

def main():
    import uvicorn
    uvicorn.run("dac_web.main:app")

if __name__=="__main__":
    main()
    # parser.add_argument("--project-folder", type=str, default=path.join(path.dirname(__file__), "../projects"))
    # parser.add_argument("--save-folder", type=str, default=path.join(path.dirname(__file__), "../projects_save"))