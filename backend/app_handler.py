import os, json
from os import path

from flask import Flask, request, jsonify
from werkzeug.routing import UnicodeConverter
from flask_cors import CORS # to be removed in final container

from matplotlib.figure import Figure
import matplotlib as mpl
from matplotlib.backends.backend_webagg import Gcf

import dac
from dac.core import Container, GCK, NodeBase, ActionNode, DataNode
from dac.core.actions import PAB, VAB, SAB
from dac.core.plugin import use_plugin
GCK_ID = 'global'
FIG_NUM = 1

class ContextKeyConverter(UnicodeConverter):
    # context key uuid or 'global'
    pass

class NodeConverter(UnicodeConverter):
    # data or action node uuid
    pass

app = Flask(__name__)
app.url_map.converters['ctx'] = ContextKeyConverter
app.url_map.converters['node'] = ContextKeyConverter
CORS(app)

current_plugin = "0.base.yaml"
plugins_dir = path.join(path.dirname(dac.__file__), "plugins")
use_plugin(path.join(plugins_dir, current_plugin))
container = Container.parse_save_config({})

# -----------
# init & save
# -----------

@app.route('/init', methods=['POST'])
def init():
    global container
    config = request.get_json()
    container = Container.parse_save_config(config)

    return jsonify({"message": "Init done"}), 200

@app.route('/save', methods=['GET'])
def get_save():
    return jsonify({
        "message": "Save done",
        "config": container.get_save_config(), # end user won't get this
    })

# -------
# plugins
# -------

@app.route('/plugins', methods=['GET', 'POST'])
def handle_plugins():
    # GET/POST => get list / activate
    global current_plugin
    class FakeDACWin:
        def message(self, s):
            pass

    if request.method=="GET":
        return jsonify({
            "plugins": os.listdir(plugins_dir),
            "current_plugin": current_plugin,
        }), 200
    else:
        target_plugin = request.get_json().get("plugin")
        use_plugin(path.join(plugins_dir, target_plugin), dac_win=FakeDACWin())
        current_plugin = target_plugin
        return jsonify({
            "message": f"Switch to '{target_plugin}'",
            "current_plugin": current_plugin,
        })
    
# --------
# contexts
# --------
    
@app.route('/contexts', methods=['GET', 'POST'])
def handle_contexts():
    # GET/POST => get list / create new
    if request.method == "GET":
        contexts = [
            {"name": node_name, "uuid": node.uuid, "type": get_nodetype_path(node_type)}
            for node_type, node_name, node
            in container.context_keys.NodeIter
        ]
        contexts.insert(0, {
            "name": "Global",
            "uuid": GCK_ID,
            "type": get_nodetype_path(GCK.__class__),
        })
        return jsonify({
            "contexts": contexts,
            "current_context": GCK_ID if container.current_key is GCK else container.current_key.uuid
        }), 200
    else:
        context_config = request.get_json().get("context_config")
        context_key_type = Container.GetClass(context_config['type'])
        context_key = context_key_type(context_config['name'])
        container.context_keys.add_node(context_key)
        
        return jsonify({
            "message": f"Create context '{context_key.name}'",
            "context_uuid": context_key.uuid
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
            "context_config": context_key.get_construct_config()
        })
    elif request.method == "PUT":
        context_config = request.get_json().get("context_config")
        if (new_name:=context_config.get("name")) and new_name!=context_key.name:
            container.context_keys.rename_node_to(context_key, new_name)
        context_key.apply_construct_config(context_config)
        return jsonify({
            "message": f"Update context '{context_key.name}'",
        })
    elif request.method == "POST":
        container.activate_context(context_key)
        return jsonify({
            "message": f"Activate context '{context_key.name}'",
        })
    elif request.method == "DELETE":
        if context_key is container.current_key:
            container.activate_context(GCK)
        container.remove_context_key(context_key)
        return jsonify({
            "message": f"Delete context '{context_key.name}'",
        })

@app.route('/types/<string:option>', methods=['GET'])
def get_available_types(option: str):
    if option == 'context':
        return jsonify({
            "context_types": [
                {"name": data_type.__name__, "type": get_nodetype_path(data_type)}
                if not isinstance(data_type, str) else
                data_type
                for data_type
                in Container.GetGlobalDataTypes()
            ]
        }), 200
    elif option == 'action':
        return jsonify({
            "action_types": [
                {"name": action_type.CAPTION, "type": get_nodetype_path(action_type)}
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
            {"name": node_name, "uuid": node.uuid, "type": get_nodetype_path(node_type)}
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
            "data_config": data.get_construct_config()
        })
    elif request.method == "PUT":
        data.apply_construct_config(request.get_json().get("data_config")) # but shouldn't be editable
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
        action_config = request.get_json().get("action_config")
        action_type = Container.GetClass(action_config['type'])
        action = action_type(context_key=context_key)
        
        container.actions.append(action)
        return jsonify({
            "message": f"Create action '{action.name}'",
            "action_uuid": action.uuid
        })
    elif request.method == "GET":
        return jsonify({"actions": [
            {"name": action.name, "uuid": action.uuid, "status": action.status}
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
            "action_config": action.get_construct_config()
        })
    elif request.method == "PUT":
        action_config = request.get_json().get("action_config")
        action.apply_construct_config(action_config)
        return jsonify({
            "message": f"Update action '{action.name}'",
        })
    elif request.method == "POST":
       msg, signal, status = run_action(action)
       return jsonify({
            "message": msg,
            "data_updated": signal,
            "status": status
       })
    elif request.method == "DELETE":
        container.actions.remove(action)
        return jsonify({
            "message": f"Delete action '{action.name}'",
        })

# ------
# others
# ------

@app.route("/ready")
def ready():
    return {}, 204

def get_context_key(context_key_id: str):
    if context_key_id == GCK_ID:
        return GCK
    else:
        try:
            return container.context_keys.get_node_by_uuid(context_key_id)
        except:
            return None

def get_nodetype_path(node_type: type[NodeBase]):
    return f"{node_type.__module__}.{node_type.__qualname__}"

def run_action(action: ActionNode, complete_cb: callable=None) -> tuple[str, bool, int]:
    params = container.prepare_params_for_action(action._SIGNATURE, action._construct_config)

    def completed(rst):
        current_context = container.CurrentContext
        if isinstance(rst, DataNode):
            rst.name = action.out_name # what if out_name is None?
            current_context.add_node(rst)
            signal = True
        elif isinstance(rst, list):
            for e_rst in rst:
                e_rst: DataNode # cautious if e_rst is not DataNode
                current_context.add_node(e_rst)
            signal = True
        else:
            signal = False

        action.status = ActionNode.ActionStatus.COMPLETE # TODO: update accordingly
        
        if callable(complete_cb):
            complete_cb()

        return signal, action.status

    action.container = container

    if isinstance(action, VAB):
        manager = Gcf.get_fig_manager(FIG_NUM)
        if manager is None:
            figure = Figure()
            # canvas not set?
        else:
            figure = manager.canvas.figure
        
        action.figure = figure

    if False: # isinstance(action, PAB):
        def fn(p, progress_emitter, logger):
            action._progress = progress_emitter
            action._message = logger
            action.pre_run()
            rst = action(**p)
            action.post_run()
            return rst
    else:
        action.pre_run()
        rst = action(**params)
        action.post_run()
        return f"Run action '{action.name}'", *completed(rst)

# @app.route("/progress")
# @app.route("/terminate")
# @app.route("/query")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
