from os import path
from uuid import uuid4
import os

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS # to be removed in final container
from podman import PodmanClient
from podman.errors import NotFound, APIError
import subprocess, requests, json



app = Flask(__name__, static_folder="../frontend/dist/")
CORS(app)
app_entry = "backend/app_entry.py"

podman_url = 'unix:///run/podman/podman.sock'
container_image = "dac_web:latest"

SESSID_KEY = "dac-sess_id"
PROJDIR_KEY = "project_folder"
SAVEDIR_KEY = "save_folder"



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



with PodmanClient(base_url=podman_url) as client:
    @app.route("/")
    @app.route('/projects/<string:project_id>', methods=['GET']) # let frontend to load and judge
    def index():
        return send_from_directory(app.static_folder, "index.html")
    
    @app.route("/<path:filename>")
    def static_files(filename):
        # should let analysis container to serve static files?
        # so the dependencies can be maintained by container versions
        return send_from_directory(app.static_folder, filename)

    @app.route('/load', methods=['POST'])
    def load_project(project_id: str=None):
        if project_id is None:
            project_id = request.get_json().get("project_id")

        if found(project_id):

            with open(path.join(app.config[PROJDIR_KEY], project_id), mode='r') as fp:
                config = json.load(fp)['dac']

            sess_id = start_process_session()
            conn = user_manager.get_sess_conn(sess_id)
            resp = requests.post(f"http://{conn}/init", json=config)
            if resp.status_code == 200:
                return jsonify({"message": "Project loaded", SESSID_KEY: sess_id, "project_id": project_id}), 200
            else:
                return jsonify({"error": "Project load failed"}), 500
        else:
            return jsonify({"error": "Project not found"}), 404
        
    @app.route('/load_saved', methods=['POST'])
    def load_saved_project():
        project_id = get_project_id_by_path(request.get_json().get("project_path"))
        return load_project(project_id)

    @app.route('/_new_', methods=['POST'])
    def new_container_session():
        sess_id = uuid4().hex

        # # Define the path for the progress file or a shared volume
        # # This example uses a file-based approach for simplicity
        # progress_file_path = f"/path/to/progress_files/progress_{user_id}.txt"

        # # Define container volumes (shared storage between containers)
        # volumes = {"/path/to/progress_files": {"bind": "/path/to/container/progress_files", "mode": "rw"}}

        # Start a new container for the analysis module
        try:
            container = client.containers.run(
                container_image,
                ["python", app_entry],
                name=f"dac_{sess_id}", # volumes=volumes, bind port
                remove=True, detach=True
            )
            user_manager.set_sess(sess_id, "conn", container.id)

            # TODO: and return project_id?
            return jsonify({"message": "Analysis started", SESSID_KEY: sess_id}), 200
        except APIError:
            pass
        except Exception as e:
            return jsonify({"error": f"Failed to start analysis: {str(e)}"}), 500
    
    @app.route("/new", methods=['POST'])
    def new_process_session():
        sess_id = start_process_session()
        return jsonify({"message": "Analysis started", SESSID_KEY: sess_id}), 200

    @app.route('/_term_', methods=['POST'])
    def terminate_container_session():
        sess_id = request.headers.get(SESSID_KEY)
        if not user_manager.validate_sess(sess_id):
            return jsonify({"error": "Invalid or missing session ID"}), 401

        try:
            container = client.containers.get(user_manager.get_sess_obj(sess_id))
            container.remove(force=True)
            user_manager.remove_sess(sess_id)

            return jsonify({"message": "Analysis terminated"}), 200
        except NotFound:
            return jsonify({"error": "Container not found"}), 404
        except Exception as e:
            return jsonify({"error": f"Failed to terminate analysis: {str(e)}"}), 500
        
    @app.route('/term', methods=['POST'])
    def terminate_process_session():
        sess_id = request.headers.get(SESSID_KEY)
        if not user_manager.validate_sess(sess_id):
            return jsonify({"error": "Invalid or missing session ID"}), 401
        
        try:
            user_manager.get_sess_obj(sess_id).terminate()
            user_manager.remove_sess(sess_id)
            return jsonify({"message": "Analysis terminated"}), 200
        except Exception as e:
            return jsonify({"error": f"Failed to terminate analysis: {str(e)}"}), 500
        
    @app.route("/project_files", methods=['POST'])
    def get_project_files():
        relpath = request.get_json().get("relpath").strip("/")
        node_dir = path.join(app.config[SAVEDIR_KEY], relpath)

        dirpath, dirnames, filenames = next(os.walk(node_dir))
        return jsonify({"dirnames": dirnames, "filenames": filenames}), 200



# ------
# Others
# ------

def found(project_id):
    return path.isfile(path.join(app.config[PROJDIR_KEY], project_id))

def get_project_id_by_path(project_path):
    with open(path.join(app.config[SAVEDIR_KEY], project_path.strip("/")), mode='r') as fp:
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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
