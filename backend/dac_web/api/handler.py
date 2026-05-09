"""Router for applications

Create, read, save, terminate app services.
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from importlib.metadata import version
from os import path
from pathlib import Path
from uuid import uuid4

import httpx
from asyncpg import Connection
from fastapi import APIRouter, HTTPException, Request, Query, Depends

import dac_web.schema as s
from dac_web.schema import SESSID_KEY
from dac_web.db.connection import get_db
from dac_web.auth import get_current_user, get_keycloak_config, is_keycloak_enabled

logger = logging.getLogger(__name__)

router = APIRouter()

APPMOD_ENTRY = "dac_web.app.entry"
PROJDIR = os.getenv("PROJECT_DIR", "./storage/projects")
SAVEDIR = os.getenv("PROJECT_SAVE_DIR", "./storage/projects_save")
__VERSION__ = version("miz-dac_web")
LOG_DIR = os.getenv("LOG_DIR", "./storage/logs")
APP_LOG_ON = os.getenv("APP_LOG_ON")
DBSTORE = os.getenv("DBSTORE", "true").lower() in ("true", "1", "yes")


class UserManager(dict[str, tuple[str, asyncio.subprocess.Process, str | None]]):
    def validate_sess(self, sess_id: str) -> bool:
        return sess_id is not None and sess_id in self

    def set_sess(
        self, sess_id: str, conn_str: str, app_obj: asyncio.subprocess.Process,
        owner_user_id: str | None = None,
    ):
        self[sess_id] = conn_str, app_obj, owner_user_id

    def get_sess_conn(self, sess_id: str) -> str:
        conn_str, app_obj, _ = self[sess_id]
        return conn_str

    def get_sess_obj(self, sess_id: str) -> asyncio.subprocess.Process:
        conn_str, app_obj, _ = self[sess_id]
        return app_obj

    def get_sess_owner(self, sess_id: str) -> str | None:
        conn_str, app_obj, owner = self[sess_id]
        return owner

    def set_sess_owner(self, sess_id: str, owner_user_id: str):
        conn_str, app_obj, _ = self[sess_id]
        self[sess_id] = conn_str, app_obj, owner_user_id

    def remove_sess(self, sess_id: str):
        if sess_id in self:
            del self[sess_id]


user_manager = UserManager()


@router.get("/auth/status", response_model=s.KeycloakStatus)
async def auth_status():
    return s.KeycloakStatus(**get_keycloak_config())


@router.post("/load", response_model=s.ManProjectResp)
async def load_project(
    data: s.InitProjectReq,
    conn: Connection | None = Depends(get_db),
    current_user: dict | None = Depends(get_current_user),
):
    project_id = data.project_id
    if not project_id:
        raise HTTPException(status_code=400, detail="Project ID is required")

    if DBSTORE:
        if conn is None:
            raise HTTPException(status_code=503, detail="Database not available")
        config, title = await read_project_config(project_id, conn)
    else:
        config, title = await read_project_config_file(project_id)

    if config is not None:
        owner = current_user["sub"] if current_user else None
        sess_id = await start_process_session(owner_user_id=owner)
        intconnstr = user_manager.get_sess_conn(sess_id)
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"http://{intconnstr}/init", json=config, headers={SESSID_KEY: sess_id}
            )
        if resp.status_code == 200:
            return s.ManProjectResp(
                message="Project loaded",
                project_id=project_id,
                title=title,
                **{SESSID_KEY: sess_id},
            )
        else:
            raise HTTPException(status_code=500, detail="Project load failed")
    else:
        raise HTTPException(status_code=404, detail="Project not found")


@router.post("/new", response_model=s.ManProjectResp)
async def new_process_session(
    current_user: dict | None = Depends(get_current_user),
):
    owner = current_user["sub"] if current_user else None
    sess_id = await start_process_session(owner_user_id=owner)
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
        p.terminate()
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
    request: Request,
    data: s.SaveProjectReq,
    conn: Connection | None = Depends(get_db),
    current_user: dict | None = Depends(get_current_user),
):
    sess_id = request.headers.get(SESSID_KEY)
    if sess_id is None or not user_manager.validate_sess(sess_id):
        raise HTTPException(status_code=401, detail="Invalid or missing session ID")

    project_id = data.project_id
    title = data.title

    creator_name = None
    if current_user is not None:
        signature = current_user["sub"]
        creator_name = current_user.get("given_name") and current_user.get("family_name") and \
            f"{current_user['given_name']} {current_user['family_name']}" or \
            current_user.get("given_name") or current_user.get("preferred_username") or ""
        owner = user_manager.get_sess_owner(sess_id)
        if owner is None:
            user_manager.set_sess_owner(sess_id, signature)
        elif owner != signature:
            raise HTTPException(
                status_code=403, detail="Session is owned by another user"
            )
    else:
        if is_keycloak_enabled():
            raise HTTPException(status_code=401, detail="Authentication required to save")
        signature = data.signature or ""

    intconnstr = user_manager.get_sess_conn(sess_id)
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"http://{intconnstr}/save", headers={SESSID_KEY: sess_id})

    if resp.status_code == 200:
        config = resp.json()["config"]

        user_id = current_user["sub"] if current_user else None

        if DBSTORE:
            if conn is None:
                raise HTTPException(status_code=503, detail="Database not available")
            fin_project_id = await save_project_config(
                project_id, config, title, signature, conn, user_id, creator_name
            )
        else:
            fin_project_id = await save_project_config_file(
                project_id, config, title, signature, user_id, creator_name
            )

        return s.ManProjectResp(
            message="Project saved",
            project_id=fin_project_id,
            title=data.title or title,
            **{SESSID_KEY: None},
        )
    else:
        raise HTTPException(status_code=500, detail="Project save failed")


# ------
# Others
# ------


async def start_process_session(owner_user_id: str | None = None):
    sess_id = uuid4().hex

    process = await asyncio.create_subprocess_exec(
        sys.executable,
        "-m",
        APPMOD_ENTRY,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    try:
        bline = await asyncio.wait_for(process.stdout.readline(), timeout=10.0)
    except asyncio.TimeoutError:
        process.kill()
        raise HTTPException(status_code=500, detail="Subprocess startup timed out")
    port = bline.decode().split("...")[-1].strip()
    user_manager.set_sess(sess_id, f"localhost:{port}", process, owner_user_id)

    return sess_id


# -------------
# Projects & DB
# -------------


@router.get("/projects", response_model=s.ProjectListResp)
async def get_project_list(
    conn: Connection | None = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, le=100),
):
    if conn is None:
        raise HTTPException(status_code=503, detail="Database not available")

    offset = (page - 1) * page_size

    where_clause = "WHERE n.valid = TRUE"

    count_row = await conn.fetchrow(
        f"SELECT COUNT(*) as total FROM nodes n {where_clause}"
    )
    total = count_row["total"]

    rows = await conn.fetch(
        f"""
        SELECT n.id, n.created_at, n.updated_at,
               n.content->'dac_web'->>'title' as title,
               n.content->'dac_web'->>'creator_name' as creator_name
        FROM nodes n
        {where_clause}
        ORDER BY n.created_at DESC
        LIMIT $1 OFFSET $2
        """,
        page_size,
        offset,
    )

    projects = [
        s.ProjectItem(
            id=str(r["id"]),
            created_at=r["created_at"].isoformat(),
            updated_at=r["updated_at"].isoformat(),
            title=r["title"],
            creator_name=r["creator_name"],
        )
        for r in rows
    ]

    return s.ProjectListResp(
        message="Project list retrieved",
        projects=projects,
        total=total,
        page=page,
        page_size=page_size,
    )


async def read_project_config_file(project_id: str) -> tuple[dict | None, str | None]:
    if "/" in project_id or "\\" in project_id or ".." in project_id:
        raise HTTPException(status_code=400, detail="Invalid project ID")
    project_fpath = path.join(PROJDIR, project_id)
    if not path.isfile(project_fpath):
        return None, None
    with open(project_fpath, mode="r") as fp:
        mconfig = json.load(fp)
    return mconfig.get("dac"), mconfig.get("dac_web", {}).get("title")


async def read_project_config(project_id: str, conn: Connection) -> tuple[dict | None, str | None]:
    row = await conn.fetchrow(
        "SELECT content FROM nodes WHERE id = $1::uuid AND valid = TRUE",
        project_id,
    )
    if not row:
        return None, None
    content = json.loads(row["content"])
    return content.get("dac"), content.get("dac_web", {}).get("title")


async def save_project_config_file(
    project_id: str, config: dict, title: str, signature: str,
    user_id: str | None = None, creator_name: str | None = None,
) -> str:
    dac_web_config = {
        "signature": signature,
        "version": __VERSION__,
    }
    if title:
        dac_web_config["title"] = title
    if creator_name:
        dac_web_config["creator_name"] = creator_name

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

    if user_id:
        dac_web_config["user_id"] = user_id

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
    project_id: str, config: dict, title: str, signature: str, conn: Connection,
    user_id: str | None = None, creator_name: str | None = None,
) -> str:
    dac_web: dict = {"version": __VERSION__}
    if title:
        dac_web["title"] = title
    if creator_name:
        dac_web["creator_name"] = creator_name
    content = {"dac": config, "dac_web": dac_web}

    async with conn.transaction():
        if not project_id or project_id=="new":
            r = await conn.fetchrow(
                "INSERT INTO nodes (content, creator_signature, user_id, valid) VALUES ($1::jsonb, $2, $3, TRUE) RETURNING id",
                json.dumps(content),
                signature,
                user_id,
            )
            final_id = str(r["id"])
        else:
            row = await conn.fetchrow(
                "SELECT creator_signature FROM nodes WHERE id = $1::uuid",
                project_id,
            )
            if row:
                if (existing_sig := row["creator_signature"]) is None or existing_sig != signature:
                    r = await conn.fetchrow(
                        "INSERT INTO nodes (content, creator_signature, user_id, valid) VALUES ($1::jsonb, $2, $3, TRUE) RETURNING id",
                        json.dumps(content),
                        signature,
                        user_id,
                    )
                    final_id = str(r["id"])
                    await conn.execute(
                        "INSERT INTO histories (node_id, inherit_from_id) VALUES ($1::uuid, $2::uuid)",
                        final_id,
                        project_id,
                    )
                else:
                    await conn.execute(
                        "UPDATE nodes SET content = $1::jsonb, creator_signature = $2, user_id = $3 WHERE id = $4::uuid",
                        json.dumps(content),
                        signature,
                        user_id,
                        project_id,
                    )
                    final_id = project_id
            else:
                r = await conn.fetchrow(
                    "INSERT INTO nodes (content, creator_signature, user_id, valid) VALUES ($1::jsonb, $2, $3, TRUE) RETURNING id",
                    json.dumps(content),
                    signature,
                    user_id,
                )
                final_id = str(r["id"])

    return final_id

