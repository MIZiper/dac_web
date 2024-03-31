import os
from os import path

from flask import Flask, request, jsonify
from werkzeug.routing import UnicodeConverter

import dac
from dac.core import Container, GCK
from dac.core.plugin import use_plugin
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

# ----
# init
# ----

@app.route('/init', methods=['POST'])
def init():
    config = request.json
    global container
    container = Container.parse_save_config(config)

    return jsonify({"message": "Init done"}), 200

# -------
# plugins
# -------

@app.route('/plugins', methods=['GET', 'POST'])
def handle_plugins():
    class FakeDACWin:
        def message(self, s):
            pass

    plugins_dir = path.join(path.dirname(dac.__file__), "plugins")
    if request.method=="GET":
        return jsonify({
            "data": os.listdir(plugins_dir)
        })
    else:
        target_plugin = request.get_json().get("data")
        use_plugin(path.join(plugins_dir, target_plugin), dac_win=FakeDACWin())
        return jsonify({
            "message": f"Switch to {target_plugin}"
        })
    
# --------
# contexts
# --------
    
@app.route('/contexts', method=['GET', 'POST'])
def handle_contexts():
    pass

@app.route('/contexts/<ctx:context_key_id>', methods=['GET', 'PUT', 'POST', 'DELETE'])
def handle_context_of(context_key_id: str):
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

# ----
# data
# ----

@app.route('/<ctx:context_key_id>/data', methods=['GET', 'POST'])
def handle_data(context_key_id: str):
    if context_key_id == GCK_ID:
        context_key = GCK
    else:
        for node_type, node_name, node in container.context_keys.NodeIter:
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

@app.route('/<ctx:context_key_id>/data/<node:data_id>', methods=['GET', 'PUT', 'POST', 'DELETE'])
def handle_data_of(context_key_id: str, data_id: str):
    # GET/PUT/POST/DELETE => get_config/set_config/.../delete
    pass

# -------
# actions
# -------

@app.route('/<ctx:context_key_id>/actions', methods=['GET', 'POST'])
def handle_actions(context_key_id: str):
    if context_key_id == GCK_ID:
        context_key = GCK
    else:
        for node_type, node_name, node in container.context_keys.NodeIter:
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

@app.route('/<ctx:context_key_id>/actions/<node:action_id>', methods=['GET', 'PUT', 'POST', 'DELETE'])
def handle_action_of(context_key_id: str, action_id: str):
    # GET/PUT/POST/DELETE => get_config/set_config/exec/delete
    pass

# ------
# others
# ------

# @app.route("/progress")
# @app.route("/terminate")
# @app.route("/query")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
