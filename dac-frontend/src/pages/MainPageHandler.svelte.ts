import type { ActionItem, ActionType, DataItem, ScenarioItem } from "../schema";
import { ax_api, ax_app } from "../utils/FetchObjects";
import { DEFAULT_NAME, SESSID_KEY, GCK_ID } from "../utils/FetchObjects";

let data: DataItem[] = $state([]);
let actions: ActionItem[] = $state([]);
let contexts: DataItem[] = $state([]);
let scenarios: ScenarioItem[] = $state([]);
let availableContextTypes: ActionType[] = $state([]);
let availableActionTypes: ActionType[] = $state([]);

// const sha1 = new Hashes.SHA1();

export function stateObjectPasser() {
    return { data, actions, contexts, scenarios, availableContextTypes, availableActionTypes };
}

export async function initAnalysis(sess_id: string) {
    ax_app.defaults.headers.common[SESSID_KEY] = sess_id;
    ax_api.defaults.headers.common[SESSID_KEY] = sess_id;

    const currentContext: DataItem = {
        name: "GCK",
        uuid: GCK_ID,
        type_path: "",
    };

    await Promise.all([
        fetchScenarios(),
        fetchContextTypes(),
        fetchActionTypes(),
        getCurrentData(currentContext),
        getCurrentActions(currentContext),
    ])

    window.addEventListener("beforeunload", function (e) {
        navigator.sendBeacon('/api/term', JSON.stringify({ [SESSID_KEY]: sess_id }));
        // POST only triggered when refreshing page or to same domain or with the prevent dialog
        // navigator.sendBeacon is async and works
    });
}

export async function fetchScenarios() {
    const res = await ax_app.get("/scenarios");
    if (res.status == 200) {
        scenarios = res.data["scenarios"];
        return res.data["current_scenario"];
    } else {
        throw new Error(`Error while fetching scenarios: ${res.status}`);
        console.error(res);
    }
}

export async function getCurrentData(context: DataItem) {
    const res = await ax_app.get(`/${context.uuid}/data`);
    data = res.data['data'];
}

export async function getCurrentActions(context: DataItem) {
    const res = await ax_app.get(`/${context.uuid}/actions`);
    actions = res.data['actions'];

}

export async function switchScenario(scenario: ScenarioItem) {
    const res = await ax_app.post("/scenarios", {
        scenario: scenario.name
    });
    if (res.status == 200) {
        return res.data['current_scenario'];
        // fetch others
    }
}

export async function fetchContextTypes() {
    const res = await ax_app.get("/types/context");
    availableContextTypes = res.data['context_types'];
}

export async function fetchActionTypes() {
    const res = await ax_app.get("/types/action");
    availableActionTypes = res.data['action_types'];
}

export async function addContext(contextType: ActionType) {
    if (contexts.find(
        (c) => (c.type_path === contextType.type_path) && (c.name === DEFAULT_NAME)
    )) {
        console.error("Context already exists.");
        return;
    }

    const res = await ax_app.post("/contexts", {
        context_config: {
            type: contextType.type_path,
            name: DEFAULT_NAME,
        }
    });

    if (res.status == 200) {
        contexts.push({
            name: DEFAULT_NAME,
            uuid: res.data["context_uuid"],
            type_path: contextType.type_path,
        });
    }
}

export async function updateContext(context: DataItem, context_config: any) {
    const res = await ax_app.put(`/contexts/${context.uuid}`, {
        context_config: context_config
    });
    if (res.status == 200) {
        context.name = context_config["name"];
    }
}

export async function getContextConfig(context: DataItem) {
    const res = await ax_app.get(`/contexts/${context.uuid}`);
    return res.data['context_config'];
}

export async function deleteContext(context: DataItem) {
    const res = await ax_app.delete(`/contexts/${context.uuid}`);
    if (res.status == 200) {
        contexts = contexts.filter((c) => c.uuid !== context.uuid);
    }
}

export async function addAction(context: DataItem, actionType: ActionType) {
    const res = await ax_app.post(`/${context.uuid}/actions`, {
        action_config: {
            type: actionType.type_path,
            name: actionType.type_name, // this is actually ignored
        }
    });
    actions.push({
        name: actionType.type_name,
        uuid: res.data['action_uuid'],
        status: "New",
    });
}

export async function updateAction(context: DataItem, action: ActionItem, action_config: any) {
    const res = await ax_app.put(`/${context.uuid}/actions/${action.uuid}`, {
        action_config: action_config
    });
    // actions = actions.map((a)=>{
    //     if (a.uuid === action.uuid) {
    //         a.name = action_config.name;
    //         a.status = "Configured";
    //     }
    //     return a;
    // });
    action.name = action_config['name'];
    action.status = "Configured";
}

export async function getActionConfig(context: DataItem, action: ActionItem) {
    const res = await ax_app.get(`/${context.uuid}/actions/${action.uuid}`);
    return res.data['action_config'];
}

export async function runAction(context: DataItem, action: ActionItem) {
    const res = await ax_app.post(`/${context.uuid}/actions/${action.uuid}`);
}

export async function deleteAction(context: DataItem, action: ActionItem) {
    const res = await ax_app.delete(`/${context.uuid}/actions/${action.uuid}`);
    actions = actions.filter((a) => a.uuid !== action.uuid);
}

export async function saveProject(publish_name: string = "", signature: string = "") {
    const res = await ax_api.post("/save", {
        // signature: sha1.hex(signature),
        project_id: "",
        publish_name: publish_name || null,
    });
}