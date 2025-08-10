import os, json
from os import path

from fastapi import FastAPI, Request, HTTPException, Body, Path as FPath
from fastapi.responses import JSONResponse

from matplotlib.figure import Figure
import matplotlib as mpl
from matplotlib.backends.backend_webagg import Gcf

import dac
from dac.core import Container, GCK, NodeBase, ActionNode, DataNode
from dac.core.actions import PAB, VAB, SAB
from dac.core.plugin import use_plugin

GCK_ID = 'global'
FIG_NUM = 1

app = FastAPI()

current_plugin = "0.base.yaml"
plugins_dir = path.join(path.dirname(dac.__file__), "plugins")
use_plugin(path.join(plugins_dir, current_plugin))
container = Container.parse_save_config({})

# -----------
# init & save
# -----------

@app.post('/init')
async def init(config: dict = Body(...)):
    global container
    container = Container.parse_save_config(config)
    return {"message": "Init done"}

@app.get('/save')
async def get_save():
    return {
        "message": "Save done",
        "config": container.get_save_config(),
    }

# -------
# plugins
# -------

@app.get('/plugins')
async def get_plugins():
    return {
        "plugins": os.listdir(plugins_dir),
        "current_plugin": current_plugin,
    }

@app.post('/plugins')
async def post_plugins(data: dict = Body(...)):
    global current_plugin
    class FakeDACWin:
        def message(self, s):
            pass
    target_plugin = data.get("plugin")
    use_plugin(path.join(plugins_dir, target_plugin), dac_win=FakeDACWin())
    current_plugin = target_plugin
    return {
        "message": f"Switch to '{target_plugin}'",
        "current_plugin": current_plugin,
    }

# --------
# contexts
# --------

@app.get('/contexts')
async def get_contexts():
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
    return {
        "contexts": contexts,
        "current_context": GCK_ID if container.current_key is GCK else container.current_key.uuid
    }

@app.post('/contexts')
async def post_contexts(data: dict = Body(...)):
    context_config = data.get("context_config")
    context_key_type = Container.GetClass(context_config['type'])
    context_key = context_key_type(context_config['name'])
    container.context_keys.add_node(context_key)
    return {
        "message": f"Create context '{context_key.name}'",
        "context_uuid": context_key.uuid
    }

@app.get('/contexts/{context_key_id}')
async def get_context_of(context_key_id: str = FPath(...)):
    context_key = get_context_key(context_key_id)
    if context_key is None:
        raise HTTPException(status_code=404, detail="No such context key")
    return {
        "context_config": context_key.get_construct_config()
    }

@app.put('/contexts/{context_key_id}')
async def put_context_of(context_key_id: str, data: dict = Body(...)):
    context_key = get_context_key(context_key_id)
    if context_key is None or context_key is GCK:
        raise HTTPException(status_code=400, detail="Cannot modify global context key")
    context_config = data.get("context_config")
    if (new_name:=context_config.get("name")) and new_name!=context_key.name:
        container.context_keys.rename_node_to(context_key, new_name)
    context_key.apply_construct_config(context_config)
    return {
        "message": f"Update context '{context_key.name}'",
    }

@app.post('/contexts/{context_key_id}')
async def post_context_of(context_key_id: str):
    context_key = get_context_key(context_key_id)
    if context_key is None:
        raise HTTPException(status_code=404, detail="No such context key")
    container.activate_context(context_key)
    return {
        "message": f"Activate context '{context_key.name}'",
    }

@app.delete('/contexts/{context_key_id}')
async def delete_context_of(context_key_id: str):
    context_key = get_context_key(context_key_id)
    if context_key is None or context_key is GCK:
        raise HTTPException(status_code=400, detail="Cannot delete global context key")
    if context_key is container.current_key:
        container.activate_context(GCK)
    container.remove_context_key(context_key)
    return {
        "message": f"Delete context '{context_key.name}'",
    }

@app.get('/types/{option}')
async def get_available_types(option: str):
    if option == 'context':
        return {
            "context_types": [
                {"name": data_type.__name__, "type": get_nodetype_path(data_type)}
                if not isinstance(data_type, str) else
                data_type
                for data_type
                in Container.GetGlobalDataTypes()
            ]
        }
    elif option == 'action':
        return {
            "action_types": [
                {"name": action_type.CAPTION, "type": get_nodetype_path(action_type)}
                if not isinstance(action_type, str) else
                action_type
                for action_type
                in container.ActionTypesInCurrentContext
            ]
        }
    else:
        raise HTTPException(status_code=404, detail="Unrecognized command")

# ----
# data
# ----

@app.get('/{context_key_id}/data')
async def get_data(context_key_id: str):
    context_key = get_context_key(context_key_id)
    if context_key is None:
        raise HTTPException(status_code=404, detail="No such context key")
    context = container.get_context(context_key)
    return {
        "data": [
            {"name": node_name, "uuid": node.uuid, "type": get_nodetype_path(node_type)}
            for node_type, node_name, node
            in context.NodeIter
        ]
    }

@app.get('/{context_key_id}/data/{data_id}')
async def get_data_of(context_key_id: str, data_id: str):
    context_key = get_context_key(context_key_id)
    if context_key is None:
        raise HTTPException(status_code=404, detail="No such context key")
    context = container.get_context(context_key)
    data = context.get_node_by_uuid(data_id)
    if data is None:
        raise HTTPException(status_code=404, detail="No such data")
    return {
        "data_config": data.get_construct_config()
    }

@app.put('/{context_key_id}/data/{data_id}')
async def put_data_of(context_key_id: str, data_id: str, data_body: dict = Body(...)):
    context_key = get_context_key(context_key_id)
    if context_key is None:
        raise HTTPException(status_code=404, detail="No such context key")
    context = container.get_context(context_key)
    data = context.get_node_by_uuid(data_id)
    if data is None:
        raise HTTPException(status_code=404, detail="No such data")
    data.apply_construct_config(data_body.get("data_config"))
    return {
        "message": f"Update data '{data.name}'",
    }

# -------
# actions
# -------

@app.get('/{context_key_id}/actions')
async def get_actions(context_key_id: str):
    context_key = get_context_key(context_key_id)
    if context_key is None:
        raise HTTPException(status_code=404, detail="No such context key")
    context = container.get_context(context_key)
    return {
        "actions": [
            {"name": action.name, "uuid": action.uuid, "status": action.status}
            for action
            in container.actions
            if action.context_key is context_key
        ]
    }

@app.post('/{context_key_id}/actions')
async def post_actions(context_key_id: str, data: dict = Body(...)):
    context_key = get_context_key(context_key_id)
    if context_key is None:
        raise HTTPException(status_code=404, detail="No such context key")
    action_config = data.get("action_config")
    action_type = Container.GetClass(action_config['type'])
    action = action_type(context_key=context_key)
    container.actions.append(action)
    return {
        "message": f"Create action '{action.name}'",
        "action_uuid": action.uuid
    }

@app.get('/{context_key_id}/actions/{action_id}')
async def get_action_of(context_key_id: str, action_id: str):
    context_key = get_context_key(context_key_id)
    if context_key is None:
        raise HTTPException(status_code=404, detail="No such context key")
    action = next(filter(lambda a: a.uuid == action_id, container.actions), None)
    if action is None:
        raise HTTPException(status_code=404, detail="No such action")
    return {
        "action_config": action.get_construct_config()
    }

@app.put('/{context_key_id}/actions/{action_id}')
async def put_action_of(context_key_id: str, action_id: str, data: dict = Body(...)):
    context_key = get_context_key(context_key_id)
    if context_key is None:
        raise HTTPException(status_code=404, detail="No such context key")
    action = next(filter(lambda a: a.uuid == action_id, container.actions), None)
    if action is None:
        raise HTTPException(status_code=404, detail="No such action")
    action_config = data.get("action_config")
    action.apply_construct_config(action_config)
    return {
        "message": f"Update action '{action.name}'",
    }

@app.post('/{context_key_id}/actions/{action_id}')
async def post_action_of(context_key_id: str, action_id: str):
    context_key = get_context_key(context_key_id)
    if context_key is None:
        raise HTTPException(status_code=404, detail="No such context key")
    action = next(filter(lambda a: a.uuid == action_id, container.actions), None)
    if action is None:
        raise HTTPException(status_code=404, detail="No such action")
    msg, signal, status = run_action(action)
    return {
        "message": msg,
        "data_updated": signal,
        "status": status
    }

@app.delete('/{context_key_id}/actions/{action_id}')
async def delete_action_of(context_key_id: str, action_id: str):
    context_key = get_context_key(context_key_id)
    if context_key is None:
        raise HTTPException(status_code=404, detail="No such context key")
    action = next(filter(lambda a: a.uuid == action_id, container.actions), None)
    if action is None:
        raise HTTPException(status_code=404, detail="No such action")
    container.actions.remove(action)
    return {
        "message": f"Delete action '{action.name}'",
    }

# ------
# others
# ------

@app.get("/ready")
async def ready():
    return JSONResponse(status_code=204, content={})

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
            rst.name = action.out_name
            current_context.add_node(rst)
            signal = True
        elif isinstance(rst, list):
            for e_rst in rst:
                e_rst: DataNode
                current_context.add_node(e_rst)
            signal = True
        else:
            signal = False

        action.status = ActionNode.ActionStatus.COMPLETE
        if callable(complete_cb):
            complete_cb()
        return signal, action.status

    action.container = container

    if isinstance(action, VAB):
        manager = Gcf.get_fig_manager(FIG_NUM)
        if manager is None:
            figure = Figure()
        else:
            figure = manager.canvas.figure
        action.figure = figure

    if False:
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
