import type { ActionItem, ActionStatus, ActionType, DataItem, ScenarioItem } from "../schema";
import { ax_api, ax_app } from "../utils/FetchObjects";
import { DEFAULT_NAME, SESSID_KEY, GCK_ID } from "../utils/FetchObjects";

export const appdata: {
    data: DataItem[],
    actions: ActionItem[],
    contexts: DataItem[],
    scenarios: ScenarioItem[],
    availableContextTypes: ActionType[],
    availableActionTypes: ActionType[],
    currentContext: DataItem | null,
    currentScenario: ScenarioItem | null,
} = $state({
    data: [],
    actions: [],
    contexts: [],
    scenarios: [],
    availableActionTypes: [],
    availableContextTypes: [],
    currentContext: null,
    currentScenario: null,
});

const statusMap: Map<number, ActionStatus> = new Map([
    [0, "New"],
    [1, "Configured"],
    [2, "Completed"],
    [-1, "Failed"],
]);

// const sha1 = new Hashes.SHA1();

export async function initAnalysis(sess_id: string) {
    ax_app.defaults.headers.common[SESSID_KEY] = sess_id;
    ax_api.defaults.headers.common[SESSID_KEY] = sess_id;

    await Promise.all([
        fetchScenarios(),
        fetchContextTypes(),
        fetchContexts(),
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
        appdata.scenarios = res.data["scenarios"].map(
            (n: string) => ({
                name: n,
            })
        );
        appdata.currentScenario = {
            name: res.data["current_scenario"]
        };
    } else {
        throw new Error(`Error while fetching scenarios: ${res.status}`);
        console.error(res);
    }
}

export async function fetchContexts() {
    const res = await ax_app.get('/contexts');
    appdata.contexts = res.data['contexts'].map((c: any) => ({
        name: c['name'],
        uuid: c['uuid'],
        type_path: c['type'],
    }));
    appdata.currentContext = appdata.contexts.find((c) => c.uuid === res.data['current_context']) || null;
}

export async function getCurrentData(context: DataItem) {
    const res = await ax_app.get(`/${context.uuid}/data`);
    appdata.data = res.data['data'].map((d: any) => ({
        name: d['name'],
        uuid: d['uuid'],
        type_path: "",
    }));
}

export async function getCurrentActions(context: DataItem) {
    const res = await ax_app.get(`/${context.uuid}/actions`);
    appdata.actions = res.data['actions'].map((a: any) => ({
        name: a["name"],
        uuid: a["uuid"],
        status: statusMap.get(a['status']),
    }));
}

export async function switchScenario(scenario: ScenarioItem) {
    const res = await ax_app.post("/scenarios", {
        scenario: scenario.name
    });
    if (res.status == 200) {
        scenario.name === res.data['current_scenario'];
        await Promise.all([
            fetchContextTypes(),
            fetchActionTypes(),
        ]);
    }
}

export async function switchContext(context: DataItem) {
    const res = await ax_app.post(`/contexts/${context.uuid}`);
    if (res.status == 200) {
        await Promise.all([
            getCurrentData(context),
            getCurrentActions(context),
            fetchActionTypes(),
        ]);
    }
}

export async function fetchContextTypes() {
    const res = await ax_app.get("/types/context");
    appdata.availableContextTypes = res.data['context_types'].map((e: any) => ({
        type_name: e['name'],
        type_path: e['type'],
    }));
}

export async function fetchActionTypes() {
    const res = await ax_app.get("/types/action");
    appdata.availableActionTypes = res.data['action_types'].map((t: any) => {
        if (typeof t === "string") {
            return {
                type_name: t,
                type_path: null,
            }
        } else {
            return {
                type_name: t['name'],
                type_path: t['type'],
            }
        }
    });
}

export async function addContext(contextType: ActionType) {
    if (appdata.contexts.find(
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
        appdata.contexts.push({
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
        appdata.contexts = appdata.contexts.filter((c) => c.uuid !== context.uuid);
    }
}

export async function addAction(context: DataItem, actionType: ActionType) {
    const res = await ax_app.post(`/${context.uuid}/actions`, {
        action_config: {
            type: actionType.type_path,
            name: actionType.type_name, // this is actually ignored
        }
    });
    appdata.actions.push({
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
    appdata.actions = appdata.actions.filter((a) => a.uuid !== action.uuid);
}

export async function saveProject(publish_name: string = "", signature: string = "") {
    const res = await ax_api.post("/save", {
        // signature: sha1.hex(signature),
        project_id: "",
        publish_name: publish_name || null,
    });
}