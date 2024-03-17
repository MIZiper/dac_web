from flask import Flask, request, jsonify, send_from_directory
import uuid
from podman import PodmanClient
from podman.errors import NotFound

app = Flask(__name__, static_folder="../frontend/dist/")
analysis_entry = "backend/analysis.py"

# Podman configuration
podman_url = 'unix:///run/podman/podman.sock'
container_image = "dac_web:latest"

# Placeholder for tracking user containers
user_containers = {}

with PodmanClient(base_url=podman_url) as client:

    @app.route("/")
    def index():
        return send_from_directory(app.static_folder, "index.html")
    
    @app.route("/<path:filename>")
    def static_files(filename):
        return send_from_directory(app.static_folder, filename)

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
                ["python", analysis_entry],
                name=f"analysis_{sess_id}", # volumes=volumes,
                remove=True, detach=True
            )
            user_containers[sess_id] = container.id

            # TODO: and return project_id?
            return jsonify({"message": "Analysis started", "dac-sess_id": sess_id}), 200
        except Exception as e:
            return jsonify({"error": f"Failed to start analysis: {str(e)}"}), 500
        
    @app.route('/projects/<uuid:project_id', methods=['GET'])
    def load_project(project_id):
        sess_id = request.headers.get('dac-sess_id')
        if sess_id:
            pass
        else: # newly created, start a container
            pass

    @app.route('/progress', methods=['GET'])
    def get_progress():
        user_id = request.args.get('user_id')
        if not user_id or user_id not in user_containers:
            return jsonify({"error": "Invalid or missing User ID"}), 400

        # Logic to retrieve progress for the user's analysis task
        progress = "50%"  # Placeholder for actual progress tracking mechanism
        return jsonify({"user_id": user_id, "progress": progress}), 200

    @app.route('/terminate', methods=['POST'])
    def terminate_analysis():
        user_id = request.json.get('user_id')
        if not user_id or user_id not in user_containers:
            return jsonify({"error": "Invalid or missing User ID"}), 400

        try:
            container = client.containers.get(user_containers[user_id])
            container.remove(force=True)
            del user_containers[user_id]
            return jsonify({"message": "Analysis terminated"}), 200
        except NotFound:
            return jsonify({"error": "Container not found"}), 404
        except Exception as e:
            return jsonify({"error": f"Failed to terminate analysis: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
