"""Router for applications

Create, read, save, terminate app services.
"""

import os, asyncio, httpx, json, socket
import sys
from os import path
from pathlib import Path
from uuid import uuid4
from datetime import datetime
from importlib.metadata import version

from fastapi import FastAPI, Request, HTTPException, Body, APIRouter

router = APIRouter()

APPMOD_ENTRY = "dac_web.app.__init__"
SESSID_KEY = "dac-sess_id"
PROJDIR = os.getenv("PROJECT_DIR", "./storage/projects")
SAVEDIR = os.getenv("PROJECT_SAVE_DIR", "./storage/projects_save")
__VERSION__ = version("miz-dac_web")
LOG_DIR = os.getenv("LOG_DIR", "./storage/logs")
APP_LOG_ON = os.getenv("APP_LOG_ON")


class UserManager(dict):
    def validate_sess(self, sess_id: str):
        return sess_id is not None and sess_id in self

    def set_sess(
        self, sess_id: str, conn_str: str, app_obj: asyncio.subprocess.Process
    ):
        self[sess_id] = conn_str, app_obj

    def get_sess_conn(self, sess_id: str) -> str:
        conn_str, app_obj = self[sess_id]
        return conn_str

    def get_sess_obj(self, sess_id: str) -> asyncio.subprocess.Process:
        conn_str, app_obj = self[sess_id]
        return app_obj

    def remove_sess(self, sess_id: str):
        if sess_id in self:
            del self[sess_id]


user_manager = UserManager()


@router.post("/load")
async def load_project(data: dict = Body(...)):
    project_id = data.get("project_id")
    project_fpath = path.join(PROJDIR, project_id)
    if path.isfile(project_fpath):
        with open(project_fpath, mode="r") as fp:
            config = json.load(fp)["dac"]

        sess_id = await start_process_session()
        conn = user_manager.get_sess_conn(sess_id)
        async with httpx.AsyncClient() as client:
            resp = await client.post(f"http://{conn}/init", json=config)
        if resp.status_code == 200:
            return {
                "message": "Project loaded",
                SESSID_KEY: sess_id,
                "project_id": project_id,
            }
        else:
            raise HTTPException(status_code=500, detail="Project load failed")
    else:
        raise HTTPException(status_code=404, detail="Project not found")


@router.post("/load_saved")
async def load_saved_project(data: dict = Body(...)):
    project_id = get_project_id_by_path(data.get("project_path"))
    return await load_project({"project_id": project_id})


@router.post("/new")
async def new_process_session():
    sess_id = await start_process_session()
    return {"message": "Analysis started", SESSID_KEY: sess_id}


@router.post("/term")
async def terminate_process_session(request: Request):
    sess_id = (await request.json()).get(SESSID_KEY)
    if not user_manager.validate_sess(sess_id):
        raise HTTPException(status_code=401, detail="Invalid or missing session ID")
    try:
        p = user_manager.get_sess_obj(sess_id)
        p.terminate()  # terminate first to flush out the outputs, otherwise below code blocks. strange but works.
        # NOTE: it is said PIPE has a buffer limit, no idea what if output is long since it's always in demo phase :|
        if APP_LOG_ON and LOG_DIR:
            out, err = await p.communicate()
            stdout_path = path.join(
                LOG_DIR, f"{datetime.now().strftime('%Y%m%d%H%M%S')}-{sess_id}.out.log"
            )
            stderr_path = path.join(
                LOG_DIR, f"{datetime.now().strftime('%Y%m%d%H%M%S')}-{sess_id}.err.log"
            )
            Path(stdout_path).write_bytes(out or b"")
            Path(stderr_path).write_bytes(err or b"")
        user_manager.remove_sess(sess_id)
        return {"message": "Analysis terminated"}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to terminate analysis: {str(e)}"
        )


@router.post("/save")
async def save_project(request: Request, data: dict = Body(...)):
    sess_id = request.headers.get(SESSID_KEY)
    if not user_manager.validate_sess(sess_id):
        raise HTTPException(status_code=401, detail="Invalid or missing session ID")
    project_id = data.get("project_id", "").strip("./")
    publish_name = data.get("publish_name", "").strip("./")
    signature = data.get("signature")

    dac_web_config = {
        "signature": signature,
        "version": __VERSION__,
    }

    if project_id:
        project_fpath = path.join(PROJDIR, project_id)
        if path.isfile(project_fpath):
            with open(project_fpath, mode="r") as fp:
                config = json.load(fp)
            config_web = config.get("dac_web", {})
            if "signature" not in config_web or config_web["signature"] != signature:
                dac_web_config["inherit"] = project_id
                project_id = uuid4().hex
    else:
        project_id = uuid4().hex

    conn = user_manager.get_sess_conn(sess_id)
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"http://{conn}/save")
    if resp.status_code == 200:
        project_fpath = path.join(PROJDIR, project_id)
        config = resp.json()
        with open(project_fpath, mode="w") as fp:
            json.dump(
                {
                    "dac": config["config"],
                    "dac_web": dac_web_config,
                },
                fp,
                indent=2,
            )

        if publish_name:
            save_fpath = path.join(SAVEDIR, publish_name)
            lines = ""
            if path.isfile(save_fpath):
                with open(save_fpath, mode="r") as fp:
                    lines = fp.read()
            with open(save_fpath, mode="w") as fp:
                line = f"{project_id}; {datetime.now()}; {signature}\n"
                fp.write(line)
                fp.write(lines)
        return {"message": "Project saved", "project_id": project_id}
    else:
        raise HTTPException(status_code=500, detail="Project save failed")


# @router.post("/project_files")
async def get_project_files(data: dict = Body(...)):
    relpath = data.get("relpath").strip("./")
    node_dir = path.join(SAVEDIR, relpath)
    dirpath, dirnames, filenames = next(os.walk(node_dir))
    return {"dirnames": dirnames, "filenames": filenames}  # TODO: filter out .gitkeep


# ------
# Others
# ------


def get_project_id_by_path(project_path):
    with open(path.join(SAVEDIR, project_path.strip("./")), mode="r") as fp:
        project_id = fp.readline().split(";")[0].strip()

    return project_id


async def start_process_session():
    sess_id = uuid4().hex

    # env = os.environ.copy()
    # env['APP_SESSID'] = sess_id

    process = await asyncio.create_subprocess_exec(
        sys.executable,
        "-m",
        APPMOD_ENTRY,
        # env=env,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    bline = await process.stdout.readline()
    port = bline.decode().split("...")[-1].strip()
    user_manager.set_sess(sess_id, f"localhost:{port}", process)

    return sess_id
