from flask import Flask, request, jsonify
from podman import PodmanClient
from podman.errors import NotFound

app = Flask(__name__)
analysis_entry = "backend/analysis.py"

# Podman configuration
podman_url = 'unix:///run/podman/podman.sock'
container_image = "dac_web:latest"

# Placeholder for tracking user containers
user_containers = {}

with PodmanClient(base_url=podman_url) as client:

    @app.route('/start', methods=['POST'])
    def start_analysis():
        user_id = request.json.get('user_id')
        if not user_id:
            return jsonify({"error": "User ID is required"}), 400

        # # Define the path for the progress file or a shared volume
        # # This example uses a file-based approach for simplicity
        # progress_file_path = f"/path/to/progress_files/progress_{user_id}.txt"

        # # Define container volumes (shared storage between containers)
        # volumes = {"/path/to/progress_files": {"bind": "/path/to/container/progress_files", "mode": "rw"}}

        # Start a new container for the analysis module
        try:
            container = client.containers.run(container_image,
                                               ["python", analysis_entry],
                                               name=f"analysis_{user_id}",
                                               # volumes=volumes,
                                               remove=True,
                                               detach=True)
            user_containers[user_id] = container.id
            return jsonify({"message": "Analysis started", "container_id": container.id}), 200
        except Exception as e:
            return jsonify({"error": f"Failed to start analysis: {str(e)}"}), 500

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