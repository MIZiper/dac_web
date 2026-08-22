"""Router for applications

Create, read, save, terminate app services.
"""

import asyncio
import json
import logging
import sys
import time
import glob as _glob
from datetime import datetime
from importlib.metadata import version
from os import path
from pathlib import Path
from uuid import uuid4

import httpx
import psutil
from asyncpg import Connection
from fastapi import APIRouter, HTTPException, Request, Query, Depends

import traceback as _traceback
from datetime import timezone as _timezone

import dac_web.schema as s
from dac_web.schema import SESSID_KEY
from dac_web.config import settings
from dac_web.db.connection import get_db
from dac_web.auth import get_current_user, get_keycloak_config, is_keycloak_enabled, require_admin

logger = logging.getLogger(__name__)

router = APIRouter()

APPMOD_ENTRY = "dac_web.app.entry"
PROJDIR = settings.project_dir
SAVEDIR = settings.project_save_dir
__VERSION__ = version("miz-dac_web")
LOG_DIR = settings.log_dir
APP_LOG_ON = settings.app_log_on
DBSTORE = settings.dbstore
STDERR_RING_SIZE = settings.log_buffer_size
STDERR_TAIL_SIZE = 20


class UserManager(dict[str, tuple[str, asyncio.subprocess.Process, str | None]]):
    def __init__(self):
        super().__init__()
        self._stderr_buffers: dict[str, list[str]] = {}
        self._stderr_tasks: dict[str, asyncio.Task] = {}
        self._stdout_buffers: dict[str, list[str]] = {}
        self._stdout_tasks: dict[str, asyncio.Task] = {}
        self._created_at: dict[str, float] = {}
        self._project_id: dict[str, str | None] = {}
        self._resource_stats: dict[str, dict] = {}
        self._process_handles: dict[str, psutil.Process] = {}

    def validate_sess(self, sess_id: str) -> bool:
        return sess_id is not None and sess_id in self

    def set_sess(
        self, sess_id: str, conn_str: str, app_obj: asyncio.subprocess.Process,
        owner_user_id: str | None = None,
    ):
        self[sess_id] = conn_str, app_obj, owner_user_id
        self._stderr_buffers[sess_id] = []
        self._stdout_buffers[sess_id] = []
        self._created_at[sess_id] = time.time()

    def set_project_id(self, sess_id: str, project_id: str | None):
        self._project_id[sess_id] = project_id

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

    def get_stderr_tail(self, sess_id: str, n: int = STDERR_TAIL_SIZE) -> str:
        buf = self._stderr_buffers.get(sess_id, [])
        return "\n".join(buf[-n:])

    def start_stderr_reader(self, sess_id: str, process: asyncio.subprocess.Process):
        async def _reader():
            buf = self._stderr_buffers.get(sess_id, [])
            try:
                while process.stderr:
                    line = await process.stderr.readline()
                    if not line:
                        break
                    decoded = line.decode(errors="replace").rstrip("\n")
                    buf.append(decoded)
                    if len(buf) > STDERR_RING_SIZE:
                        del buf[: len(buf) - STDERR_RING_SIZE]
                    logger.debug("subprocess stderr [%s]: %s", sess_id[:8], decoded)
            except Exception:
                pass
        self._stderr_tasks[sess_id] = asyncio.create_task(_reader())

    def stop_stderr_reader(self, sess_id: str):
        task = self._stderr_tasks.pop(sess_id, None)
        if task and not task.done():
            task.cancel()

    def start_stdout_reader(self, sess_id: str, process: asyncio.subprocess.Process):
        async def _reader():
            buf = self._stdout_buffers.get(sess_id, [])
            try:
                while process.stdout:
                    line = await process.stdout.readline()
                    if not line:
                        break
                    decoded = line.decode(errors="replace").rstrip("\n")
                    buf.append(decoded)
                    if len(buf) > STDERR_RING_SIZE:
                        del buf[: len(buf) - STDERR_RING_SIZE]
                    logger.debug("subprocess stdout [%s]: %s", sess_id[:8], decoded)
            except Exception:
                pass
        self._stdout_tasks[sess_id] = asyncio.create_task(_reader())

    def stop_stdout_reader(self, sess_id: str):
        task = self._stdout_tasks.pop(sess_id, None)
        if task and not task.done():
            task.cancel()

    def get_logs(self, sess_id: str) -> tuple[str, str, str | None, str | None]:
        """Return (stdout, stderr, log_file_stdout, log_file_stderr) for a session.

        For active sessions, returns buffer contents.
        For terminated sessions, checks LOG_DIR for saved log files.
        """
        if sess_id in self:
            stdout_buf = self._stdout_buffers.get(sess_id, [])
            stderr_buf = self._stderr_buffers.get(sess_id, [])
            return "\n".join(stdout_buf), "\n".join(stderr_buf), None, None

        log_out = None
        log_err = None
        if LOG_DIR:
            stdout_files = _glob.glob(path.join(LOG_DIR, f"*-{sess_id}.out.log"))
            stderr_files = _glob.glob(path.join(LOG_DIR, f"*-{sess_id}.err.log"))
            if stdout_files:
                log_out = stdout_files[0]
            if stderr_files:
                log_err = stderr_files[0]
        return "", "", log_out, log_err

    def remove_sess(self, sess_id: str):
        if sess_id in self:
            del self[sess_id]
        self.stop_stderr_reader(sess_id)
        self.stop_stdout_reader(sess_id)
        self._stderr_buffers.pop(sess_id, None)
        self._stdout_buffers.pop(sess_id, None)
        self._created_at.pop(sess_id, None)
        self._project_id.pop(sess_id, None)
        self._resource_stats.pop(sess_id, None)
        self._process_handles.pop(sess_id, None)

    async def _cleanup_orphans(self):
        while True:
            await asyncio.sleep(300)
            dead = []
            for sess_id, (_, p, _) in list(self.items()):
                if p.returncode is not None:
                    dead.append(sess_id)
            for sess_id in dead:
                logger.info("Removing orphaned session: %s", sess_id)
                self.remove_sess(sess_id)

    async def _collect_resources(self):
        while True:
            await asyncio.sleep(10)
            for sess_id, (_, process, _) in list(self.items()):
                if process.returncode is not None:
                    prev = self._resource_stats.get(sess_id, {})
                    self._resource_stats[sess_id] = {
                        "cpu_percent": prev.get("cpu_percent"),
                        "memory_rss": prev.get("memory_rss"),
                        "status": f"exited({process.returncode})",
                        "pid": process.pid,
                    }
                    continue
                try:
                    if sess_id not in self._process_handles:
                        self._process_handles[sess_id] = psutil.Process(process.pid)
                    p = self._process_handles[sess_id]
                    cpu = p.cpu_percent()
                    mem = p.memory_info().rss
                    self._resource_stats[sess_id] = {
                        "cpu_percent": round(cpu, 1),
                        "memory_rss": mem,
                        "status": "running",
                        "pid": process.pid,
                    }
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    self._resource_stats[sess_id] = {
                        "cpu_percent": None,
                        "memory_rss": None,
                        "status": "exited" if process.returncode is not None else "zombie",
                        "pid": process.pid,
                    }
                except Exception:
                    pass


user_manager = UserManager()


def _make_error_response(
    status_code: int,
    message: str,
    exc: BaseException | None = None,
    endpoint: str = "",
    sess_id: str = "",
) -> s.DACErrorResponse:
    detail = None
    if settings.debug:
        tb = ""
        if exc:
            tb = "".join(
                _traceback.format_exception(type(exc), exc, exc.__traceback__)
            )
        stderr = ""
        if sess_id:
            stderr = user_manager.get_stderr_tail(sess_id)
        detail = s.DACErrorDetail(
            traceback=tb,
            stderr=stderr,
            endpoint=endpoint,
            timestamp=datetime.now(_timezone.utc).isoformat(),
        )
    logger.error(
        "API error %d: %s%s",
        status_code,
        message,
        f"\n{detail.traceback}" if detail and detail.traceback else "",
    )
    return s.DACErrorResponse(code=status_code, message=message, detail=detail)


def _raise_http(status_code: int, message: str, exc: BaseException | None = None, endpoint: str = "", sess_id: str = ""):
    err = _make_error_response(status_code, message, exc, endpoint, sess_id)
    raise HTTPException(status_code=status_code, detail=err.model_dump())


@router.get("/auth/status", response_model=s.KeycloakStatus)
async def auth_status():
    config = get_keycloak_config()
    config["admin_role"] = settings.admin_role
    config["admin_available"] = is_keycloak_enabled() or bool(settings.admin_token) or True
    return s.KeycloakStatus(**config)


@router.post("/load", response_model=s.ManProjectResp)
async def load_project(
    data: s.InitProjectReq,
    conn: Connection | None = Depends(get_db),
    current_user: dict | None = Depends(get_current_user),
):
    project_id = data.project_id
    if not project_id:
        _raise_http(400, "Project ID is required", endpoint="/api/load")

    if DBSTORE:
        if conn is None:
            _raise_http(503, "Database not available", endpoint="/api/load")
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
            user_manager.set_project_id(sess_id, project_id)
            return s.ManProjectResp(
                message="Project loaded",
                project_id=project_id,
                title=title,
                **{SESSID_KEY: sess_id},
            )
        else:
            sub_err = ""
            try:
                sub_err = resp.text
            except Exception:
                pass
            _raise_http(
                500,
                f"Project load failed: subprocess returned {resp.status_code}" + (f" — {sub_err}" if settings.debug else ""),
                endpoint="/api/load",
                sess_id=sess_id,
            )
    else:
        _raise_http(404, "Project not found", endpoint="/api/load")


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
        _raise_http(401, "Invalid or missing session ID", endpoint="/api/term")
    try:
        p = user_manager.get_sess_obj(sess_id)
        p.terminate()
        if APP_LOG_ON and LOG_DIR:
                user_manager.stop_stderr_reader(sess_id)
                user_manager.stop_stdout_reader(sess_id)
                await p.wait()
                stdout_content = "\n".join(user_manager._stdout_buffers.get(sess_id, []))
                stderr_content = "\n".join(user_manager._stderr_buffers.get(sess_id, []))
                stdout_path = path.join(
                    LOG_DIR, f"{datetime.now().strftime('%Y%m%d%H%M%S')}-{sess_id}.out.log"
                )
                stderr_path = path.join(
                    LOG_DIR, f"{datetime.now().strftime('%Y%m%d%H%M%S')}-{sess_id}.err.log"
                )
                await asyncio.to_thread(Path(stdout_path).write_text, stdout_content)
                await asyncio.to_thread(Path(stderr_path).write_text, stderr_content)
        user_manager.remove_sess(sess_id)
        return s.DACResponse(
            message="Analysis terminated",
        )
    except Exception as e:
        _raise_http(
            500,
            f"Failed to terminate analysis: {str(e)}",
            exc=e,
            endpoint="/api/term",
            sess_id=sess_id,
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
        _raise_http(401, "Invalid or missing session ID", endpoint="/api/save")

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
            _raise_http(
                403, "Session is owned by another user", endpoint="/api/save"
            )
    else:
        if is_keycloak_enabled():
            _raise_http(401, "Authentication required to save", endpoint="/api/save")
        signature = data.signature or ""

    intconnstr = user_manager.get_sess_conn(sess_id)
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"http://{intconnstr}/save", headers={SESSID_KEY: sess_id})

    if resp.status_code == 200:
        config = resp.json()["config"]

        user_id = current_user["sub"] if current_user else None

        if DBSTORE:
            if conn is None:
                _raise_http(503, "Database not available", endpoint="/api/save")
            fin_project_id = await save_project_config(
                project_id, config, title, signature, conn, user_id, creator_name
            )
        else:
            fin_project_id = await save_project_config_file(
                project_id, config, title, signature, user_id, creator_name
            )

        user_manager.set_project_id(sess_id, fin_project_id)
        return s.ManProjectResp(
            message="Project saved",
            project_id=fin_project_id,
            title=data.title or title,
            **{SESSID_KEY: None},
        )
    else:
        sub_err = ""
        try:
            sub_err = resp.text
        except Exception:
            pass
        _raise_http(
            500,
            f"Project save failed: subprocess returned {resp.status_code}" + (f" — {sub_err}" if settings.debug else ""),
            endpoint="/api/save",
            sess_id=sess_id,
        )


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

    user_manager.set_sess(sess_id, "", process, owner_user_id)
    user_manager.start_stderr_reader(sess_id, process)

    try:
        bline = await asyncio.wait_for(process.stdout.readline(), timeout=10.0)
    except asyncio.TimeoutError:
        process.kill()
        _raise_http(
            500,
            "Subprocess startup timed out",
            endpoint="/api/new",
            sess_id=sess_id,
        )
    port = bline.decode().split("...")[-1].strip()
    user_manager[sess_id] = (f"localhost:{port}", process, owner_user_id)
    user_manager.start_stdout_reader(sess_id, process)

    return sess_id


# ----------
# Admin APIs
# ----------


@router.get("/admin/sessions", response_model=s.AdminSessionsResp)
async def admin_list_sessions(
    _: None = Depends(require_admin),
):
    sessions: list[s.SessionInfo] = []
    for sess_id, (conn_str, process, owner) in user_manager.items():
        created_at = user_manager._created_at.get(sess_id, 0)
        uptime = time.time() - created_at if created_at else 0
        stats = user_manager._resource_stats.get(sess_id, {})
        sessions.append(s.SessionInfo(
            sess_id=sess_id,
            pid=process.pid,
            owner_user_id=owner,
            project_id=user_manager._project_id.get(sess_id),
            conn_str=conn_str,
            created_at=datetime.fromtimestamp(created_at, _timezone.utc).isoformat() if created_at else "",
            uptime_seconds=round(uptime, 1),
            cpu_percent=stats.get("cpu_percent"),
            memory_rss_mb=round(stats["memory_rss"] / 1024 / 1024, 1) if stats.get("memory_rss") else None,
            returncode=process.returncode,
            status=stats.get("status", "running" if process.returncode is None else f"exited({process.returncode})"),
        ))
    return s.AdminSessionsResp(sessions=sessions, total=len(sessions))


@router.post("/admin/sessions/{sess_id}/term", response_model=s.DACResponse)
async def admin_terminate_session(
    sess_id: str,
    _: None = Depends(require_admin),
):
    if not user_manager.validate_sess(sess_id):
        _raise_http(404, "Session not found", endpoint="/api/admin/sessions/term")
    try:
        p = user_manager.get_sess_obj(sess_id)
        p.terminate()
        if APP_LOG_ON and LOG_DIR:
            user_manager.stop_stderr_reader(sess_id)
            user_manager.stop_stdout_reader(sess_id)
            await p.wait()
            stdout_content = "\n".join(user_manager._stdout_buffers.get(sess_id, []))
            stderr_content = "\n".join(user_manager._stderr_buffers.get(sess_id, []))
            stdout_path = path.join(
                LOG_DIR, f"{datetime.now().strftime('%Y%m%d%H%M%S')}-{sess_id}.out.log"
            )
            stderr_path = path.join(
                LOG_DIR, f"{datetime.now().strftime('%Y%m%d%H%M%S')}-{sess_id}.err.log"
            )
            await asyncio.to_thread(Path(stdout_path).write_text, stdout_content)
            await asyncio.to_thread(Path(stderr_path).write_text, stderr_content)
        user_manager.remove_sess(sess_id)
        return s.DACResponse(message=f"Session {sess_id} terminated")
    except Exception as e:
        _raise_http(500, f"Failed to terminate: {str(e)}", exc=e, endpoint="/api/admin/sessions/term")


@router.get("/admin/sessions/{sess_id}/logs", response_model=s.SessionLogs)
async def admin_session_logs(
    sess_id: str,
    _: None = Depends(require_admin),
):
    stdout_buf, stderr_buf, log_out, log_err = user_manager.get_logs(sess_id)

    stdout_content = stdout_buf
    stderr_content = stderr_buf

    if log_out:
        try:
            stdout_content = await asyncio.to_thread(Path(log_out).read_text)
        except Exception:
            pass
    if log_err:
        try:
            stderr_content = await asyncio.to_thread(Path(log_err).read_text)
        except Exception:
            pass

    if not stdout_content and not stderr_content and not log_out and not log_err:
        _raise_http(404, "No logs found for this session", endpoint="/api/admin/sessions/logs")

    return s.SessionLogs(
        sess_id=sess_id,
        stdout=stdout_content,
        stderr=stderr_content,
        log_file_stdout=log_out,
        log_file_stderr=log_err,
    )


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
        _raise_http(503, "Database not available", endpoint="/api/projects")

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


async def read_project_full_config_file(project_id: str) -> dict | None:
    if "/" in project_id or "\\" in project_id or ".." in project_id:
        _raise_http(400, "Invalid project ID")
    project_fpath = path.join(PROJDIR, project_id)
    if not path.isfile(project_fpath):
        return None
    content = await asyncio.to_thread(Path(project_fpath).read_text)
    return json.loads(content)


async def read_project_config_file(project_id: str) -> tuple[dict | None, str | None]:
    if "/" in project_id or "\\" in project_id or ".." in project_id:
        _raise_http(400, "Invalid project ID")
    project_fpath = path.join(PROJDIR, project_id)
    if not path.isfile(project_fpath):
        return None, None
    content = await asyncio.to_thread(Path(project_fpath).read_text)
    mconfig = json.loads(content)
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
            content = await asyncio.to_thread(Path(project_fpath).read_text)
            mconfig = json.loads(content)
            config_web = mconfig.get("dac_web", {})
            if "signature" not in config_web or config_web["signature"] != signature:
                dac_web_config["inherit"] = project_id
                fin_project_id = uuid4().hex
    else:
        fin_project_id = uuid4().hex

    if user_id:
        dac_web_config["user_id"] = user_id

    project_fpath = path.join(PROJDIR, fin_project_id)
    content_str = json.dumps(
        {
            "dac": config,
            "dac_web": dac_web_config,
        },
        indent=2,
    )
    await asyncio.to_thread(Path(project_fpath).write_text, content_str)

    return fin_project_id


@router.get("/projects/{project_id}/export", response_model=s.ProjectExportResp)
async def export_project(
    project_id: str,
    conn: Connection | None = Depends(get_db),
    current_user: dict | None = Depends(get_current_user),
):
    if DBSTORE:
        if conn is None:
            _raise_http(503, "Database not available", endpoint="/api/projects/{project_id}/export")
        row = await conn.fetchrow(
            "SELECT content FROM nodes WHERE id = $1::uuid AND valid = TRUE",
            project_id,
        )
        if not row:
            _raise_http(404, "Project not found", endpoint="/api/projects/{project_id}/export")
        content = json.loads(row["content"])
    else:
        content = await read_project_full_config_file(project_id)
        if content is None:
            _raise_http(404, "Project not found", endpoint="/api/projects/{project_id}/export")

    dac_config = content.get("dac", {})
    dac_web_full = content.get("dac_web", {})
    dac_web_meta = {
        k: v for k, v in dac_web_full.items()
        if k not in ("signature", "user_id")
    }

    return s.ProjectExportResp(
        message="Project exported",
        project_id=project_id,
        config=s.ProjectConfig(
            dac=s.DACConfig.model_validate(dac_config) if dac_config else s.DACConfig(contexts=[], actions=[]),
            dac_web=dac_web_meta,
        ),
    )


@router.post("/projects/import", response_model=s.ProjectImportResp)
async def import_project(
    data: s.ProjectImportReq,
    conn: Connection | None = Depends(get_db),
    current_user: dict | None = Depends(get_current_user),
):
    unified = data.config
    dac_config = unified.dac.model_dump()
    dac_web_meta = unified.dac_web or {}
    project_id = data.project_id
    title = dac_web_meta.get("title", "")

    creator_name = dac_web_meta.get("creator_name")
    if current_user is not None:
        signature = current_user["sub"]
        if not creator_name:
            creator_name = (
                current_user.get("given_name")
                and current_user.get("family_name")
                and f"{current_user['given_name']} {current_user['family_name']}"
                or current_user.get("given_name")
                or current_user.get("preferred_username")
                or ""
            )
    else:
        if is_keycloak_enabled():
            _raise_http(401, "Authentication required to import", endpoint="/api/projects/import")
        signature = data.signature or ""

    user_id = current_user["sub"] if current_user else None

    if DBSTORE:
        if conn is None:
            _raise_http(503, "Database not available", endpoint="/api/projects/import")
        fin_project_id = await save_project_config(
            project_id, dac_config, title, signature, conn, user_id, creator_name
        )
    else:
        fin_project_id = await save_project_config_file(
            project_id, dac_config, title, signature, user_id, creator_name
        )

    return s.ProjectImportResp(
        message="Project imported",
        project_id=fin_project_id,
        title=title or None,
    )


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
    content_json = json.dumps(content)

    async with conn.transaction():
        if not project_id or project_id=="new":
            r = await conn.fetchrow(
                "INSERT INTO nodes (content, creator_signature, user_id, valid) VALUES ($1::jsonb, $2, $3, TRUE) RETURNING id",
                content_json,
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
                        content_json,
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
                        content_json,
                        signature,
                        user_id,
                        project_id,
                    )
                    final_id = project_id
            else:
                r = await conn.fetchrow(
                    "INSERT INTO nodes (content, creator_signature, user_id, valid) VALUES ($1::jsonb, $2, $3, TRUE) RETURNING id",
                    content_json,
                    signature,
                    user_id,
                )
                final_id = str(r["id"])

    return final_id


# ── Two-phase import with action replacement ──


@router.post("/projects/import-preview", response_model=s.ImportPreviewResp)
async def import_preview(data: s.ImportPreviewReq):
    """Preview action replacements for a project config before importing.

    Runs all registered replacement rules against every action and returns
    a report the user can review and approve/reject/edit.
    """
    from dac_web.import_replace import ReplacementRegistry, ReplacementStatus

    registry = ReplacementRegistry.instance()
    config = data.config
    dac_config = config.dac.model_dump() if hasattr(config.dac, "model_dump") else config.dac
    outcomes = await registry.process_all(dac_config)
    actions = dac_config.get("actions", [])

    replacements: list[s.ActionReplacementItem] = []
    resolved = unresolved = unchanged = 0

    for i, outcome in enumerate(outcomes):
        original = actions[i] if i < len(actions) else {}
        item = s.ActionReplacementItem(
            action_index=i,
            action_uuid=original.get("_uuid_", ""),
            original=original,
            replacement=outcome.action,
            status=outcome.status,
            summary=outcome.summary,
            reason=outcome.reason,
        )
        if outcome.status == ReplacementStatus.RESOLVED:
            resolved += 1
        elif outcome.status == ReplacementStatus.UNRESOLVED:
            unresolved += 1
        else:
            unchanged += 1
        replacements.append(item)

    return s.ImportPreviewResp(
        message="Preview complete",
        replacements=replacements,
        summary=s.ImportPreviewSummary(
            total_actions=len(actions),
            resolved=resolved,
            unresolved=unresolved,
            unchanged=unchanged,
        ),
    )


@router.post("/projects/import-apply", response_model=s.ImportApplyResp)
async def import_apply(
    data: s.ImportApplyReq,
    conn: Connection | None = Depends(get_db),
    current_user: dict | None = Depends(get_current_user),
):
    """Apply user-approved replacement decisions and save the project."""
    dac_config = (
        data.config.dac.model_dump()
        if hasattr(data.config.dac, "model_dump")
        else data.config.dac
    )
    actions: list[dict] = dac_config.get("actions", [])
    decisions_by_index = {d.action_index: d for d in data.decisions}

    final_actions: list[dict] = []
    for i, action in enumerate(actions):
        decision = decisions_by_index.get(i)
        if decision is None or not decision.approved:
            final_actions.append(action)
            continue
        override = decision.override_replacement
        if override:
            merged = {**action, **override}
            merged.setdefault("_uuid_", action.get("_uuid_", ""))
            final_actions.append(merged)
        else:
            # Use the replacement proposed during preview — re-run the rule
            from dac_web.import_replace import ReplacementRegistry
            registry = ReplacementRegistry.instance()
            outcome = await registry.process(action)
            if outcome.action is not None:
                final_actions.append(outcome.action)
            else:
                final_actions.append(action)

    final_config = {**dac_config, "actions": final_actions}

    dac_web_meta = data.config.dac_web or {}
    title = data.title or dac_web_meta.get("title", "")
    creator_name = dac_web_meta.get("creator_name")
    project_id = None

    if current_user is not None:
        signature = current_user["sub"]
        if not creator_name:
            creator_name = (
                current_user.get("given_name")
                and current_user.get("family_name")
                and f"{current_user['given_name']} {current_user['family_name']}"
                or current_user.get("given_name")
                or current_user.get("preferred_username")
                or ""
            )
    else:
        if is_keycloak_enabled():
            _raise_http(
                401, "Authentication required to import", endpoint="/api/projects/import-apply"
            )
        signature = data.signature or ""

    user_id = current_user["sub"] if current_user else None

    if DBSTORE:
        if conn is None:
            _raise_http(503, "Database not available", endpoint="/api/projects/import-apply")
        fin_project_id = await save_project_config(
            project_id, final_config, title, signature, conn, user_id, creator_name
        )
    else:
        fin_project_id = await save_project_config_file(
            project_id, final_config, title, signature, user_id, creator_name
        )

    return s.ImportApplyResp(
        message="Project imported with replacements applied",
        project_id=fin_project_id,
        title=title or None,
    )

