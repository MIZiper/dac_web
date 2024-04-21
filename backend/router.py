from flask import Flask, request, jsonify, send_from_directory
import uuid
from podman import PodmanClient
from podman.errors import NotFound, APIError

app = Flask(__name__, static_folder="../frontend/dist/")
analysis_entry = "backend/analysis.py"

# Podman configuration
podman_url = 'unix:///run/podman/podman.sock'
container_image = "dac_web:latest"

# Placeholder for tracking user containers
user_containers = {}
SESSID_KEY = "dac-sess_id"

def found(project_id):
    return True

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

    @app.route('/new', methods=['POST'])
    def new_session():
        sess_id = str(uuid.uuid4())

        # # Define the path for the progress file or a shared volume
        # # This example uses a file-based approach for simplicity
        # progress_file_path = f"/path/to/progress_files/progress_{user_id}.txt"

        # # Define container volumes (shared storage between containers)
        # volumes = {"/path/to/progress_files": {"bind": "/path/to/container/progress_files", "mode": "rw"}}

        # Start a new container for the analysis module
        try:
            container = client.containers.run(
                container_image,
                ["python", analysis_entry], # pass sock file
                name=f"analysis_{sess_id}", # volumes=volumes,
                remove=True, detach=True
            )
            user_containers[sess_id] = container.id

            # TODO: and return project_id?
            return jsonify({"message": "Analysis started", SESSID_KEY: sess_id}), 200
        except APIError:
            # subproc = subprocess.Popen(["python", analysis_entry]) # and pass sock file
            pass
        except Exception as e:
            return jsonify({"error": f"Failed to start analysis: {str(e)}"}), 500

    @app.route('/term', methods=['POST'])
    def terminate_session():
        sess_id = request.headers.get(SESSID_KEY)
        if not sess_id or sess_id not in user_containers:
            return jsonify({"error": "Invalid or missing session ID"}), 400

        try:
            container = client.containers.get(user_containers[sess_id])
            container.remove(force=True)
            del user_containers[sess_id]

            # or kill subprocess

            # remove sock file

            return jsonify({"message": "Analysis terminated"}), 200
        except NotFound:
            return jsonify({"error": "Container not found"}), 404
        except Exception as e:
            return jsonify({"error": f"Failed to terminate analysis: {str(e)}"}), 500
        
    @app.route('/app/<path:filename>', methods=None)
    def app_forward(filename):
        sess_id = request.headers.get(SESSID_KEY)
        if not sess_id or sess_id not in user_containers:
            return jsonify({"error": "Invalid or missing session ID"}), 400
        
        app = user_containers.get(sess_id)

if __name__ == '__main__':
    # app.config['PROJ_DIR']
    app.run(debug=True, host='0.0.0.0', port=5000)
