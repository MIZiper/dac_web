from flask import Flask, request, jsonify
import time
from dac.core import Container

app = Flask(__name__)
container = Container.parse_save_config({})

# Placeholder for actual analysis task
def perform_analysis(user_id, progress_file):
    # Simulate a long-running task with progress updates
    for progress in range(0, 101, 1):
        time.sleep(1)  # Simulate work being done
        # Update progress in a file
        with open(progress_file, 'w') as file:
            file.write(f"{progress}%")
    # Simulate completion
    with open(progress_file, 'w') as file:
        file.write("100%")

@app.route('/start', methods=['POST'])
def start():
    user_id = request.json.get('user_id')
    if not user_id:
        return jsonify({"error": "User ID is required"}), 400

    # Define a progress file unique to this user/session
    progress_file = f"progress_{user_id}.txt"

    # Start the analysis task
    perform_analysis(user_id, progress_file) # TODO: for PAB, start in subprocess

    return jsonify({"message": "Analysis started", "user_id": user_id}), 200

def get_available_plugins():
    pass

def use_plugin(name):
    pass

def get_available_actions(context_key):
    pass

def get_actions_of(context_key):
    pass

def get_data_of(context_key):
    pass

def get_config_of(node):
    pass

def apply_config_to(node):
    pass

# @app.route("/progress")
# @app.route("/terminate")
# @app.route("/query")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
