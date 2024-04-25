from os import path
from uuid import uuid4

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS # to be removed in final container
from podman import PodmanClient
from podman.errors import NotFound, APIError
import subprocess



app = Flask(__name__, static_folder="../frontend/dist/")
CORS(app)
app_entry = "backend/app_entry.py"

podman_url = 'unix:///run/podman/podman.sock'
container_image = "dac_web:latest"

SESSID_KEY = "dac-sess_id"

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
    def index():
        return send_from_directory(app.static_folder, "index.html")
    
    @app.route("/<path:filename>")
    def static_files(filename):
        # should let analysis container to serve static files?
        # so the dependencies can be maintained by container versions
        return send_from_directory(app.static_folder, filename)

    @app.route('/projects/<string:project_id>', methods=['GET'])
    def load_project(project_id):
        # projects_dir = app.config.get("PROJ_DIR", "./projects")
        if found(project_id):
            return index()
        else:
            return jsonify({"error": "Project not found"}), 404
            # redirect to index.html and notify user 404

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
            # subproc = subprocess.Popen(["python", app_entry]) # and pass port
            pass
        except Exception as e:
            return jsonify({"error": f"Failed to start analysis: {str(e)}"}), 500
    
    @app.route("/new", methods=['POST'])
    def new_process_session():
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
    
        return jsonify({"message": "Analysis started", SESSID_KEY: sess_id}), 200

    @app.route('/term', methods=['POST'])
    def terminate_session():
        sess_id = request.headers.get(SESSID_KEY)
        if not user_manager.validate_sess(sess_id):
            return jsonify({"error": "Invalid or missing session ID"}), 401

        try:
            container = client.containers.get(user_manager.get_sess_obj(sess_id))
            container.remove(force=True)
            user_manager.remove_sess(sess_id)

            # or kill subprocess
            # remove sock file

            return jsonify({"message": "Analysis terminated"}), 200
        except NotFound:
            return jsonify({"error": "Container not found"}), 404
        except Exception as e:
            return jsonify({"error": f"Failed to terminate analysis: {str(e)}"}), 500

# ------
# Others
# ------

def found(project_id):
    return True

if __name__ == '__main__':
    # app.config['PROJ_DIR']
    app.run(debug=True, host='0.0.0.0', port=5000)
