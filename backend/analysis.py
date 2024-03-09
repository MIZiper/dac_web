from flask import Flask, request, jsonify
import time

app = Flask(__name__)

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

# @app.route("/progress")
# @app.route("/terminate")
# @app.route("/query")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
