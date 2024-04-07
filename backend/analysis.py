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

plugins_dir = path.join(path.dirname(dac.__file__), "plugins")
use_plugin(path.join(plugins_dir, "0.base.yaml"))
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
    # GET/POST => get list / activate
    class FakeDACWin:
        def message(self, s):
            pass

    if request.method=="GET":
        return jsonify({
            "data": os.listdir(plugins_dir)
        })
    else:
        target_plugin = request.get_json().get("data")
        use_plugin(path.join(plugins_dir, target_plugin), dac_win=FakeDACWin())
        return jsonify({
            "message": f"Switch to '{target_plugin}'"
        })
    
# --------
# contexts
# --------
    
@app.route('/contexts', methods=['GET', 'POST'])
def handle_contexts():
    # GET/POST => get list / create new
    if request.method == "GET":
        return jsonify({
            "data": [
                (node_type.__name__, node_name, node.uuid)
                for node_type, node_name, node
                in container.context_keys.NodeIter
            ]
        }), 200
    else:
        data = request.get_json().get("data")
        context_key_type = Container.GetClass(data['type'])
        context_key = context_key_type(data['name'])
        
        return jsonify({
            "message": f"Create context '{context_key.name}'",
            "data": context_key.uuid
        })

@app.route('/contexts/<ctx:context_key_id>', methods=['GET', 'PUT', 'POST', 'DELETE'])
def handle_context_of(context_key_id: str):
    # GET/PUT/POST/DELETE => get / update / activate / delete
    if (context_key:=get_context_key(context_key_id)) is None:
        return jsonify({"error": "No such context key"}), 404
    if context_key is GCK and request.method != "POST":
        return jsonify({"error": "Cannot modify global context key"}), 400
    
    if request.method == "GET":
        return jsonify({
            "data": context_key.get_construct_config()
        })
    elif request.method == "PUT":
        data = request.get_json().get("data")
        context_key.apply_construct_config(data)
        return jsonify({
            "message": f"Update context '{context_key.name}'",
        })
    elif request.method == "POST":
        container.activate_context(context_key)
        return jsonify({
            "message": f"Activate context '{context_key.name}'",
        })
    elif request.method == "DELETE":
        container.remove_context_key(context_key)
        return jsonify({
            "message": f"Delete context '{context_key.name}'",
        })

@app.route('/types/<string:option>', methods=['GET'])
def get_available_types(option: str):
    if option == 'data':
        return jsonify({
            "data": [
                (data_type.__name__, f"{data_type.__module__}.{data_type.__qualname__}") # TODO: data_type_name should include module info
                if not isinstance(data_type, str) else
                data_type
                for data_type
                in Container.GetGlobalDataTypes()
            ]
        }), 200
    elif option == 'actions':
        return jsonify({
            "data": [
                (action_type.__name__, action_type.CAPTION) # TODO: action_type_name should include module info
                if not isinstance(action_type, str) else
                action_type
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
    # GET/POST => get list / ... (cannot add data via user)
    if (context_key:=get_context_key(context_key_id)) is None:
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
    # GET/PUT/POST/DELETE => get_config/set_config/.../delete (data not yet deletable)
    if (context_key:=get_context_key(context_key_id)) is None:
        return jsonify({"error": "No such context key"}), 404
    
    context = container.get_context(context_key)
    if (data:=context.get_node_by_uuid(data_id)) is None:
        return jsonify({"error": "No such data"}), 404
    
    if request.method == "GET":
        return jsonify({
            "data": data.get_construct_config()
        })
    elif request.method == "PUT":
        data.apply_construct_config(request.get_json().get("data"))
        return jsonify({
            "message": f"Update data '{data.name}'",
        })

# -------
# actions
# -------

@app.route('/<ctx:context_key_id>/actions', methods=['GET', 'POST'])
def handle_actions(context_key_id: str):
    # GET/POST => get list / create new
    if (context_key:=get_context_key(context_key_id)) is None:
        return jsonify({"error": "No such context key"}), 404
    
    context = container.get_context(context_key)
    if request.method == "POST":
        action_type = Container.GetClass(request.get_json().get("data")['type'])
        action = action_type(request.get_json().get("data")['name'])
        action.context_key = context_key
        container.actions.append(action)
        return jsonify({
            "message": f"Create action '{action.name}'",
            "data": action.uuid
        })
    elif request.method == "GET":
        return jsonify({"data": [
            (type(action).__name__, action.name, action.uuid)
            for action
            in container.actions
            if action.context_key is context_key
        ]}), 200

@app.route('/<ctx:context_key_id>/actions/<node:action_id>', methods=['GET', 'PUT', 'POST', 'DELETE'])
def handle_action_of(context_key_id: str, action_id: str):
    # GET/PUT/POST/DELETE => get_config/set_config/exec/delete
    if (context_key:=get_context_key(context_key_id)) is None:
        return jsonify({"error": "No such context key"}), 404

    # NOTE: action's context is not necessarily the same as the context key (current key)

    action = filter(lambda a: a.uuid == action_id, container.actions).__next__()
    if request.method == "GET":
        return jsonify({
            "data": action.get_construct_config()
        })
    elif request.method == "PUT":
        data = request.get_json().get("data")
        action.apply_construct_config(data)
        return jsonify({
            "message": f"Update action '{action.name}'",
        })
    elif request.method == "POST":
       action.exec()
    elif request.method == "DELETE":
        container.remove_action(action)
        return jsonify({
            "message": f"Delete action '{action.name}'",
        })

# ------
# others
# ------

def get_context_key(context_key_id: str):
    if context_key_id == GCK_ID:
        return GCK
    else:
        try:
            return container.context_keys.get_node_by_uuid(context_key_id)
        except:
            return None

# @app.route("/progress")
# @app.route("/terminate")
# @app.route("/query")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
