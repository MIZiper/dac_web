from os import path
from uuid import uuid4
import os
from datetime import datetime
import asyncio
from importlib.metadata import version

from fastapi import FastAPI, Request, HTTPException, Body
from fastapi.responses import JSONResponse, FileResponse
import subprocess, httpx, json



app = FastAPI()
app_entry = "dac_web.app:app"

SESSID_KEY = "dac-sess_id"
PROJDIR = os.getenv("PROJECT_DIR")
SAVEDIR = os.getenv("PROJECT_SAVE_DIR")
__VERSION__ = version("dac_web-backend")



class UserManager(dict):
    def validate_sess(self, sess_id):
        return sess_id is not None and sess_id in self

    def set_sess(self, sess_id, conn_str, app_obj):
        self[sess_id] = conn_str, app_obj

    def get_sess_conn(self, sess_id):
        conn_str, app_obj = self[sess_id]
        return conn_str

    def get_sess_obj(self, sess_id):
        conn_str, app_obj = self[sess_id]
        return app_obj

    def remove_sess(self, sess_id):
        if sess_id in self:
            del self[sess_id]

user_manager = UserManager()

@app.post('/load')
async def load_project(data: dict = Body(...)):
    project_id = data.get("project_id")
    project_fpath = path.join(PROJDIR, project_id)
    if path.isfile(project_fpath):
        with open(project_fpath, mode='r') as fp:
            config = json.load(fp)['dac']

        sess_id = start_process_session()
        conn = user_manager.get_sess_conn(sess_id)
        async with httpx.AsyncClient() as client:
            resp = await client.post(f"http://{conn}/init", json=config)
        if resp.status_code == 200:
            return {"message": "Project loaded", SESSID_KEY: sess_id, "project_id": project_id}
        else:
            raise HTTPException(status_code=500, detail="Project load failed")
    else:
        raise HTTPException(status_code=404, detail="Project not found")

@app.post('/load_saved')
async def load_saved_project(data: dict = Body(...)):
    project_id = get_project_id_by_path(data.get("project_path"))
    return await load_project({"project_id": project_id})

@app.post("/new")
async def new_process_session():
    sess_id = start_process_session()
    return {"message": "Analysis started", SESSID_KEY: sess_id}

@app.post('/term')
async def terminate_process_session(request: Request):
    sess_id = request.headers.get(SESSID_KEY)
    if not user_manager.validate_sess(sess_id):
        raise HTTPException(status_code=401, detail="Invalid or missing session ID")
    try:
        user_manager.get_sess_obj(sess_id).terminate()
        user_manager.remove_sess(sess_id)
        return {"message": "Analysis terminated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to terminate analysis: {str(e)}")

@app.post('/save')
async def save_project(request: Request, data: dict = Body(...)):
    sess_id = request.headers.get(SESSID_KEY)
    if not user_manager.validate_sess(sess_id):
        raise HTTPException(status_code=401, detail="Invalid or missing session ID")
    project_id = data.get("project_id", "").strip("./")
    publish_name  = data.get("publish_name", "").strip("./")
    signature = data.get("signature")

    dac_web_config = {
        "signature": signature,
        "version": __VERSION__,
    }

    if project_id:
        project_fpath = path.join(PROJDIR, project_id)
        if path.isfile(project_fpath):
            with open(project_fpath, mode='r') as fp:
                config = json.load(fp)
            config_web = config.get("dac_web", {})
            if "signature" not in config_web or config_web["signature"]!=signature:
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
            json.dump({
                "dac": config["config"],
                "dac_web": dac_web_config,
            }, fp, indent=2)

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

@app.post("/project_files")
async def get_project_files(data: dict = Body(...)):
    relpath = data.get("relpath").strip("./")
    node_dir = path.join(SAVEDIR, relpath)
    dirpath, dirnames, filenames = next(os.walk(node_dir))
    return {"dirnames": dirnames, "filenames": filenames}



# ------
# Others
# ------

def get_project_id_by_path(project_path):
    with open(path.join(SAVEDIR, project_path.strip("./")), mode='r') as fp:
        project_id = fp.readline().split(";")[0].strip()
    
    return project_id

def start_process_session():
    sess_id = uuid4().hex

    p_inst = subprocess.Popen(
        ["python", path.join(path.dirname(__file__), "..", app_entry), "-p", "0"],
        stdout=subprocess.PIPE,
        # stderr=subprocess.PIPE,
    )
    host_port = p_inst.stdout.readline().decode().split("...")[-1].strip()
    user_manager.set_sess(sess_id, host_port, p_inst)



    # process = await asyncio.create_subprocess_exec(
    #     'ls', '-l',
    #     stdout=asyncio.subprocess.PIPE,
    #     stderr=asyncio.subprocess.PIPE
    # )

    # stdout, stderr = await process.communicate()

    # print(f'[stdout]\n{stdout.decode()}')
    # print(f'[stderr]\n{stderr.decode()}')

    
    
    # Make sure the service is ready
    # 1)
    # print(p_inst.stdout.readline()) # >> ready <<
    # return {}, 200
    # 
    # 2)
    # import requests, time
    # for i in range(5):
    #     time.sleep(0.01)
    #     response = requests.get(f"http://{host_port}/ready")
    #     if response.status_code == 204:
    #         return jsonify({"message": "Analysis started", SESSID_KEY: sess_id}), 200
    # return jsonify({"error": "failed to connect app"}), 500

    return sess_id
