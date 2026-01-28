import os, json
from os import path

from fastapi import FastAPI, APIRouter, Request, HTTPException, Body, Path as FPath
from fastapi.responses import JSONResponse

from matplotlib.figure import Figure
from matplotlib._pylab_helpers import Gcf

import dac
from dac.core import Container, GCK, NodeBase, ActionNode, DataNode
from dac.core.actions import PAB, VAB, SAB, TAB
from dac.core.scenario import use_scenario

from dac_web.schema import Response, DACConfig, DACConfigResp, ScenariosResp

GCK_ID = "global"
FIG_NUM = 1

router = APIRouter()

current_scenario = "0.base.yaml"
scenarios_dir = os.getenv("SCENARIO_DIR") or path.join(
    path.dirname(dac.__file__), "scenarios"
)
use_scenario(path.join(scenarios_dir, current_scenario))
container = Container.parse_save_config({})

# -----------
# init & save
# -----------


@router.post("/init", response_model=Response)
async def init(config: DACConfig):
    global container
    container = Container.parse_save_config(config.model_dump())
    return Response(message="Init done")


@router.get("/save", response_model=DACConfigResp)
async def get_dac_config():
    return DACConfigResp(
        message="Saved",
        config=DACConfig.model_validate(container.get_save_config())
    )


# ---------
# scenarios
# ---------


@router.get("/scenarios", response_model=ScenariosResp)
async def list_scenarios():
    return ScenariosResp(
        message="List scenarios",
        scenarios=os.listdir(scenarios_dir),
        current_scenario=current_scenario
    )


@router.post("/scenarios")
async def switch_to_scenario(data: dict = Body(...)):
    global current_scenario

    class FakeDACWin:
        def message(self, s):
            pass

    target_scenario = data.get("scenario")
    use_scenario(path.join(scenarios_dir, target_scenario), dac_win=FakeDACWin())
    current_scenario = target_scenario
    return {
        "message": f"Switch to '{target_scenario}'",
        "current_scenario": current_scenario,
    }


# --------
# contexts
# --------


@router.get("/contexts")
async def list_contexts():
    contexts = [
        {"name": node_name, "uuid": node.uuid, "type": get_nodetype_path(node_type)}
        for node_type, node_name, node in container.context_keys.NodeIter
    ]
    contexts.insert(
        0,
        {
            "name": "Global",
            "uuid": GCK_ID,
            "type": get_nodetype_path(GCK.__class__),
        },
    )
    return {
        "contexts": contexts,
        "current_context": GCK_ID
        if container.current_key is GCK
        else container.current_key.uuid,
    }


@router.post("/contexts")
async def create_context(data: dict = Body(...)):
    context_config = data.get("context_config")
    context_key_type = Container.GetClass(context_config["type"])
    context_key = context_key_type(context_config["name"])
    container.context_keys.add_node(context_key)
    return {
        "message": f"Create context '{context_key.name}'",
        "context_uuid": context_key.uuid,
    }


@router.get("/contexts/{context_key_id}")
async def get_context_config(context_key_id: str = FPath(...)):
    context_key = get_context_key(context_key_id)
    if context_key is None:
        raise HTTPException(status_code=404, detail="No such context key")
    return {"context_config": context_key.get_construct_config()}


@router.put("/contexts/{context_key_id}")
async def update_context_config(context_key_id: str, data: dict = Body(...)):
    context_key = get_context_key(context_key_id)
    if context_key is None or context_key is GCK:
        raise HTTPException(status_code=400, detail="Cannot modify global context key")
    context_config = data.get("context_config")
    if (new_name := context_config.get("name")) and new_name != context_key.name:
        container.context_keys.rename_node_to(context_key, new_name)
    context_key.apply_construct_config(context_config)
    return {
        "message": f"Update context '{context_key.name}'",
    }


@router.post("/contexts/{context_key_id}")
async def activate_context(context_key_id: str):  # NOTE: (issue 20250813-1)
    context_key = get_context_key(context_key_id)
    if context_key is None:
        raise HTTPException(status_code=404, detail="No such context key")
    container.activate_context(context_key)
    return {
        "message": f"Activate context '{context_key.name}'",
    }


@router.delete("/contexts/{context_key_id}")
async def delete_context(context_key_id: str):
    context_key = get_context_key(context_key_id)
    if context_key is None or context_key is GCK:
        raise HTTPException(status_code=400, detail="Cannot delete global context key")
    if context_key is container.current_key:
        container.activate_context(GCK)
    container.remove_context_key(context_key)
    return {
        "message": f"Delete context '{context_key.name}'",
    }


@router.get("/types/{option}")
async def get_available_types(option: str):
    if option == "context":
        return {
            "context_types": [
                {"name": data_type.__name__, "type": get_nodetype_path(data_type)}
                if not isinstance(data_type, str)
                else data_type
                for data_type in Container.GetGlobalDataTypes()
            ]
        }
    elif option == "action":
        return {
            "action_types": [
                {"name": action_type.CAPTION, "type": get_nodetype_path(action_type)}
                if not isinstance(action_type, str)
                else action_type
                for action_type in container.ActionTypesInCurrentContext
            ]
        }
    else:
        raise HTTPException(status_code=404, detail="Unrecognized command")


# ----
# data
# ----


@router.get("/{context_key_id}/data")
async def get_context_data(context_key_id: str):
    context_key = get_context_key(context_key_id)
    if context_key is None:
        raise HTTPException(status_code=404, detail="No such context key")
    context = container.get_context(context_key)
    return {
        "data": [
            {"name": node_name, "uuid": node.uuid, "type": get_nodetype_path(node_type)}
            for node_type, node_name, node in context.NodeIter
        ]
    }


@router.get("/{context_key_id}/data/{data_id}")
async def get_data_config(context_key_id: str, data_id: str):
    context_key = get_context_key(context_key_id)
    if context_key is None:
        raise HTTPException(status_code=404, detail="No such context key")
    context = container.get_context(context_key)
    data = context.get_node_by_uuid(data_id)
    if data is None:
        raise HTTPException(status_code=404, detail="No such data")
    return {"data_config": data.get_construct_config()}


@router.put("/{context_key_id}/data/{data_id}")
async def update_data_config(context_key_id: str, data_id: str, data_body: dict = Body(...)):
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


@router.get("/{context_key_id}/actions")
async def get_actions_of_context(context_key_id: str):
    context_key = get_context_key(context_key_id)
    if context_key is None:
        raise HTTPException(status_code=404, detail="No such context key")
    context = container.get_context(context_key)
    return {
        "actions": [
            {"name": action.name, "uuid": action.uuid, "status": action.status, "type": get_nodetype_path(type(action))}
            for action in container.actions
            if action.context_key is context_key
        ]
    }


@router.post("/{context_key_id}/actions")
async def create_action_for_context(context_key_id: str, data: dict = Body(...)):
    context_key = get_context_key(context_key_id)
    if context_key is None:
        raise HTTPException(status_code=404, detail="No such context key")
    action_config = data.get("action_config")
    action_type = Container.GetClass(action_config["type"])
    action = action_type(context_key=context_key)
    container.actions.append(action)
    return {"message": f"Create action '{action.name}'", "action_uuid": action.uuid}


@router.get("/{context_key_id}/actions/{action_id}")
async def get_action_by_id(context_key_id: str, action_id: str):
    context_key = get_context_key(context_key_id)
    if context_key is None:
        raise HTTPException(status_code=404, detail="No such context key")
    action = next(filter(lambda a: a.uuid == action_id, container.actions), None)
    if action is None:
        raise HTTPException(status_code=404, detail="No such action")
    return {"action_config": action.get_construct_config()}


@router.put("/{context_key_id}/actions/{action_id}")
async def update_action_config(context_key_id: str, action_id: str, data: dict = Body(...)):
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


@router.post("/{context_key_id}/actions/{action_id}")
async def run_action_by_id(context_key_id: str, action_id: str):
    context_key = get_context_key(context_key_id)
    if context_key is None:
        raise HTTPException(status_code=404, detail="No such context key")
    action = next(filter(lambda a: a.uuid == action_id, container.actions), None)
    if action is None:
        raise HTTPException(status_code=404, detail="No such action")
    msg, signal, status, stats = run_action(action)
    return {"message": msg, "data_updated": signal, "status": status, "stats": stats}


@router.delete("/{context_key_id}/actions/{action_id}")
async def delete_action(context_key_id: str, action_id: str):
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


@router.get("/ready")
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


def run_action(
    action: ActionNode, complete_cb: callable = None
) -> tuple[str, bool, int, object]:
    params = container.prepare_params_for_action(
        action._SIGNATURE, action._construct_config
    )

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

    stats = None

    def pass_stats(data):
        nonlocal stats
        stats = data

    if isinstance(action, TAB):
        action.renderer = pass_stats

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
        data_updated, action_status = completed(rst)
        return f"Run action '{action.name}'", data_updated, action_status, stats
