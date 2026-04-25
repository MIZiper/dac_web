"""Router for applications

Create, read, save, terminate app services.
"""

import os, asyncio, httpx, json, socket
import sys
from os import path
from pathlib import Path
from uuid import uuid4, UUID
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
DBSTORE = True


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
async def load_project(data: s.InitProjectReq, conn: Connection = Depends(get_db)):
    project_id = data.project_id
    if not project_id:
        return

    if DBSTORE:
        config = await read_project_config(project_id, conn)
    else:
        config = await read_project_config_file(project_id)

    if config is not None:
        sess_id = await start_process_session()
        intconnstr = user_manager.get_sess_conn(sess_id)
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"http://{intconnstr}/init", json=config, headers={SESSID_KEY: sess_id}
            )
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
async def save_project(
    request: Request, data: s.SaveProjectReq, conn: Connection = Depends(get_db)
):
    sess_id = request.headers.get(SESSID_KEY)
    if sess_id is None or not user_manager.validate_sess(sess_id):
        raise HTTPException(status_code=401, detail="Invalid or missing session ID")

    project_id = data.project_id
    publish_name = data.publish_name
    signature = data.signature

    intconnstr = user_manager.get_sess_conn(sess_id)
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"http://{intconnstr}/save", headers={SESSID_KEY: sess_id})

    if resp.status_code == 200:
        config = resp.json()["config"]

        if DBSTORE:
            fin_project_id = await save_project_config(
                project_id, config, publish_name, signature, conn
            )
        else:
            fin_project_id = await save_project_config_file(
                project_id, config, publish_name, signature
            )

        return s.ManProjectResp(
            message="Project saved",
            project_id=fin_project_id,
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
    offset = (page - 1) * page_size
    rows = await conn.fetch(
        """
        SELECT id, created_at, updated_at
        FROM nodes
        WHERE valid = TRUE
        ORDER BY created_at DESC
        LIMIT $1 OFFSET $2
        """,
        page_size,
        offset,
    )
    return [
        {
            "id": str(r["id"]),
            "created_at": r["created_at"],
            "updated_at": r["updated_at"],
        }
        for r in rows
    ]


async def read_project_config_file(project_id: str):
    project_fpath = path.join(PROJDIR, project_id)
    if path.isfile(project_fpath):
        with open(project_fpath, mode="r") as fp:
            config = json.load(fp)["dac"]

    return config


async def read_project_config(project_id: str, conn: Connection) -> dict | None:
    # Read project configuration from DB `nodes` table where content->>'type' = 'project'
    row = await conn.fetchrow(
        "SELECT content FROM nodes WHERE id = $1::uuid AND valid = TRUE",
        project_id,
    )
    if not row:
        return None
    content = json.loads(row["content"])
    # stored format: { 'dac': {...}, 'dac_web': {...} }
    return content.get("dac")


async def save_project_config_file(
    project_id: str, config: dict, publish_name: str, signature: str
):
    dac_web_config = {
        "signature": signature,
        "version": __VERSION__,
    }

    fin_project_id = project_id
    if project_id and project_id!="new":
        project_fpath = path.join(PROJDIR, project_id)
        if path.isfile(project_fpath):
            with open(project_fpath, mode="r") as fp:
                mconfig = json.load(fp)
            config_web = mconfig.get("dac_web", {})
            if "signature" not in config_web or config_web["signature"] != signature:
                dac_web_config["inherit"] = project_id
                fin_project_id = uuid4().hex
    else:
        fin_project_id = uuid4().hex

    project_fpath = path.join(PROJDIR, fin_project_id)
    with open(project_fpath, mode="w") as fp:
        json.dump(
            {
                "dac": config,
                "dac_web": dac_web_config,
            },
            fp,
            indent=2,
        )

    return fin_project_id


async def save_project_config(
    project_id: str, config: dict, publish_name: str, signature: str, conn: Connection
):
    content = {"dac": config, "dac_web": {"version": __VERSION__}}

    # If no project_id provided, create a new node
    if not project_id or project_id=="new":
        r = await conn.fetchrow(
            "INSERT INTO nodes (content, creator_signature, valid) VALUES ($1::jsonb, $2, TRUE) RETURNING id",
            json.dumps(content),
            signature,
        )
        final_id = str(r["id"])
    else:
        # check existing node
        row = await conn.fetchrow(
            "SELECT creator_signature FROM nodes WHERE id = $1::uuid",
            project_id,
        )
        if row:
            if (existing_sig := row["creator_signature"]) is None or existing_sig != signature:
                # signature mismatch: create a new node and record inheritance
                r = await conn.fetchrow(
                    "INSERT INTO nodes (content, creator_signature, valid) VALUES ($1::jsonb, $2, TRUE) RETURNING id",
                    json.dumps(content),
                    signature,
                )
                final_id = str(r["id"])
                # record history: new node inherits from previous project_id
                await conn.execute(
                    "INSERT INTO histories (node_id, inherit_from_id) VALUES ($1::uuid, $2::uuid)",
                    final_id,
                    project_id,
                )
            else:
                # signature matches: update existing
                await conn.execute(
                    "UPDATE nodes SET content = $1::jsonb, creator_signature = $2 WHERE id = $3::uuid",
                    json.dumps(content),
                    signature,
                    project_id,
                )
                final_id = project_id
        else:
            # not found: insert
            r = await conn.fetchrow(
                "INSERT INTO nodes (content, creator_signature, valid) VALUES ($1::jsonb, $2, TRUE) RETURNING id",
                json.dumps(content),
                signature,
            )
            final_id = str(r["id"])

    # publishing: record a simple entry in publishes table if requested
    if publish_name:
        await conn.execute(
            "INSERT INTO publishes (title, node_id, status) VALUES ($1, $2::uuid, $3)",
            publish_name,
            final_id,
            "Registered",
        )

    return final_id


async def download_project_config():
    # TODO: implement download behavior if needed; currently not used
    raise HTTPException(status_code=501, detail="Not implemented")


async def overwrite_project_config():
    # TODO: implement overwrite behavior if needed; currently not used
    raise HTTPException(status_code=501, detail="Not implemented")
