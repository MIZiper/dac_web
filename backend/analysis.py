from flask import Flask, request, jsonify
from werkzeug.routing import UnicodeConverter

from dac.core import Container, GCK
GCK_ID = 'global'

class ContextKeyConverter(UnicodeConverter):
    # context key uuid or 'global'
    pass

class NodeConverter(UnicodeConverter):
    # data or action node uuid
    pass

app = Flask(__name__)
app.url_map.converters['ctx'] = ContextKeyConverter
app.url_map.converters['node'] = ContextKeyConverter

container = Container.parse_save_config({})

@app.route('/init', methods=['POST'])
def init():
    config = request.json
    global container
    container = Container.parse_save_config(config)

    return jsonify({"message": "Init done"}), 200

@app.route('/plugins', methods=['GET', 'POST'])
def handle_plugins():
    # GET -> list of available plugins
    # POST -> use plugin
    pass

@app.route('/types/<string: option>', methods=['GET'])
def get_available_types(option: str):
    if option == 'data':
        return jsonify({
            "data": [
                (data_type.__name__, data_type.__name__) # TODO: data_type_name should include module info
                for data_type
                in Container.GetGlobalDataTypes()
            ]
        }), 200
    elif option == 'actions':
        return jsonify({
            "data": [
                (action_type.__name__, action_type.CAPTION) # TODO: action_type_name should include module info
                for action_type
                in container.ActionTypesInCurrentContext
            ]
        }), 200
    else:
        return jsonify({
            "error": "Unrecognized command"
        }), 404

@app.route('/<ctx:context_key_id>/data', methods=['GET'])
def get_data_of(context_key_id: str):
    if context_key_id == GCK_ID:
        context_key = GCK
    else:
        for node_type, node_name, node in container.GlobalContext.NodeIter:
            if node.uuid==context_key_id:
                context_key = node
                break
        else:
            return jsonify({"error": "No such context key"}), 404
    
    context = container.get_context(context_key)
    return jsonify({
        "data": [
            (node_type.__name__, node_name, node.uuid)
            for node_type, node_name, node
            in context.NodeIter
        ]
    }), 200

@app.route('/<ctx:context_key_id>/actions', methods=['GET'])
def get_actions_of(context_key_id: str):
    if context_key_id == GCK_ID:
        context_key = GCK
    else:
        for node_type, node_name, node in container.GlobalContext.NodeIter:
            if node.uuid==context_key_id:
                context_key = node
                break
        else:
            return jsonify({"error": "No such context key"}), 404
        
    return jsonify({"data": [
        (type(action).__name__, action.name, action.uuid)
        for action
        in container.actions
        if action.context_key is context_key
    ]}), 200

@app.route('/<ctx:context_key_id>/data/<node:data_id>', methods=['GET', 'PUT', 'POST', 'DELETE'])
def handle_data_of(context_key_id: str, data_id: str):
    # GET/PUT/POST/DELETE => get_config/set_config/activate/delete
    pass

@app.route('/<ctx:context_key_id>/actions/<node:action_id>', methods=['GET', 'PUT', 'POST', 'DELETE'])
def handle_action_of(context_key_id: str, action_id: str):
    # GET/PUT/POST/DELETE => get_config/set_config/exec/delete
    pass

# @app.route("/progress")
# @app.route("/terminate")
# @app.route("/query")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
