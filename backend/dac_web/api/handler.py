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

from fastapi import FastAPI, Request, HTTPException, Body, APIRouter, Query, Depends
from asyncpg import Connection
import dac_web.schema as s
from dac_web.schema import SESSID_KEY
from dac_web.db.connection import get_db

router = APIRouter()

APPMOD_ENTRY = "dac_web.app.entry"
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


@router.post("/load", response_model=s.ManProjectResp)
async def load_project(data: s.InitProjectReq):
    project_id = data.project_id
    if not project_id: return
    config = await read_project_config(project_id)
    if config is not None:
        sess_id = await start_process_session()
        conn = user_manager.get_sess_conn(sess_id)
        async with httpx.AsyncClient() as client:
            resp = await client.post(f"http://{conn}/init", json=config, headers={SESSID_KEY: sess_id})
        if resp.status_code == 200:
            return s.ManProjectResp(
                message="Project loaded",
                project_id=project_id,
                **{SESSID_KEY: sess_id},
            )
        else:
            raise HTTPException(status_code=500, detail="Project load failed")
    else:
        raise HTTPException(status_code=404, detail="Project not found")



@router.post("/new", response_model=s.ManProjectResp)
async def new_process_session():
    sess_id = await start_process_session()
    return s.ManProjectResp(
        message="Analysis started",
        project_id=None,
        **{SESSID_KEY: sess_id},
    )


@router.post("/term", response_model=s.DACResponse)
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
        return s.DACResponse(
            message="Analysis terminated",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to terminate analysis: {str(e)}"
        )


@router.post("/save", response_model=s.ManProjectResp)
async def save_project(request: Request, data: s.SaveProjectReq):
    sess_id = request.headers.get(SESSID_KEY)
    if sess_id is None or not user_manager.validate_sess(sess_id):
        raise HTTPException(status_code=401, detail="Invalid or missing session ID")
    
    project_id = data.project_id
    publish_name = data.publish_name
    signature = data.signature

    project_id = await validate_project_id(project_id, signature)

    conn = user_manager.get_sess_conn(sess_id)
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"http://{conn}/save")

    if resp.status_code == 200:
        config = resp.json()

        await save_project_config(project_id, config, publish_name)

        return s.ManProjectResp(
            message="Project saved",
            project_id=project_id,
            **{SESSID_KEY: None},
        )
    else:
        raise HTTPException(status_code=500, detail="Project save failed")


# ------
# Others
# ------


async def start_process_session():
    sess_id = uuid4().hex

    process = await asyncio.create_subprocess_exec(
        sys.executable,
        "-m",
        APPMOD_ENTRY,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    bline = await process.stdout.readline()
    port = bline.decode().split("...")[-1].strip()
    user_manager.set_sess(sess_id, f"localhost:{port}", process)

    return sess_id


# -------------
# Projects & DB
# -------------


@router.get("/projects")
async def get_project_list(
    conn: Connection = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, le=100),
):
    pass

async def read_project_config(project_id: str) -> dict | None:
    project_fpath = path.join(PROJDIR, project_id)
    if path.isfile(project_fpath):
        with open(project_fpath, mode="r") as fp:
            config = json.load(fp)["dac"]

async def save_project_config(project_id: str, config: dict, publish_name: str):
    project_fpath = path.join(PROJDIR, project_id)
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

async def validate_project_id(project_id: str, signature: str) -> str:
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

async def download_project_config():
    pass

async def overwrite_project_config():
    pass