import type { ActionItem, ActionStatus, ActionType, DataItem, DataQuickAction, ScenarioItem } from "../schema";
import { ax_api, ax_app } from "../utils/FetchObjects";
import { DEFAULT_NAME, SESSID_KEY, GCK_ID } from "../utils/FetchObjects";

export const appdata: {
    data: DataItem[],
    actions: ActionItem[],
    contexts: DataItem[],
    scenarios: ScenarioItem[],
    availableContextTypes: ActionType[],
    availableActionTypes: ActionType[],
    availableQuickActions: DataQuickAction[],
    currentContext: DataItem | null,
    currentScenario: ScenarioItem | null,
    errorMessage: string,
} = $state({
    data: [],
    actions: [],
    contexts: [],
    scenarios: [],
    availableActionTypes: [],
    availableContextTypes: [],
    availableQuickActions: [],
    currentContext: null,
    currentScenario: null,
    errorMessage: '',
});

export function resetAppdata() {
    appdata.data = [];
    appdata.actions = [];
    appdata.contexts = [];
    appdata.scenarios = [];
    appdata.availableActionTypes = [];
    appdata.availableContextTypes = [];
    appdata.availableQuickActions = [];
    appdata.currentContext = null;
    appdata.currentScenario = null;
    appdata.errorMessage = '';
}

export const statusMap: Map<number, ActionStatus> = new Map([
    [0, "New"],
    [1, "Configured"],
    [2, "Completed"],
    [-1, "Failed"],
]);

function handleError(context: string, e: unknown) {
    const msg = e instanceof Error ? e.message : String(e);
    console.error(`Error in ${context}:`, e);
    appdata.errorMessage = msg;
}

export async function initAnalysis(sess_id: string): Promise<() => void> {
    const controller = new AbortController();

    const beforeunloadHandler = () => {
        navigator.sendBeacon('/api/term', JSON.stringify({ [SESSID_KEY]: sess_id }));
    };
    window.addEventListener("beforeunload", beforeunloadHandler);

    try {
        ax_app.defaults.headers.common[SESSID_KEY] = sess_id;
        ax_api.defaults.headers.common[SESSID_KEY] = sess_id;

        const initContext: DataItem = {
            name: "GlobContext",
            uuid: GCK_ID,
            type_path: "",
            children: [],
        }

        await Promise.all([
            fetchScenarios(),
            fetchContextTypes(),
            fetchContexts(),
            fetchActionTypes(),
            getCurrentData(initContext),
            getCurrentActions(initContext),
        ])
    } catch (e) {
        handleError("initAnalysis", e);
        throw e;
    }

    return () => {
        controller.abort();
        window.removeEventListener("beforeunload", beforeunloadHandler);
        ax_api.post("/term", { [SESSID_KEY]: sess_id }).catch(() => {});
    };
}

export async function fetchScenarios() {
    try {
        const res = await ax_app.get("/scenarios");
        if (res.status == 200) {
            appdata.scenarios = res.data["scenarios"].map(
                (n: string) => ({ name: n })
            );
            appdata.currentScenario = appdata.scenarios.find(
                (s) => s.name === res.data["current_scenario"]
            ) || null;
            appdata.availableQuickActions = res.data['quick_actions'] || [];
        } else {
            throw new Error(`Failed to fetch scenarios: ${res.status}`);
        }
    } catch (e) {
        handleError("fetchScenarios", e);
        throw e;
    }
}

export async function fetchContexts() {
    try {
        const res = await ax_app.get('/contexts');
        appdata.contexts = (res.data['contexts'] || []).map(
            (c: { name: string; uuid: string; type: string }) => ({
                name: c['name'],
                uuid: c['uuid'],
                type_path: c['type'],
                children: [],
            })
        );
        appdata.currentContext = appdata.contexts.find(
            (c) => c.uuid === res.data['current_context']
        ) || null;
    } catch (e) {
        handleError("fetchContexts", e);
    }
}

export async function getCurrentData(context: DataItem) {
    try {
        const res = await ax_app.get(`/${context.uuid}/data`);
        const _build = (d: { name: string; uuid: string; type: string; children?: any[] }): DataItem => ({
            name: d['name'],
            uuid: d['uuid'],
            type_path: d['type'],
            children: d['children'] ? d['children'].map((c) => _build(c)) : [],
        });
        appdata.data = (res.data['data'] || []).map((d: any) => _build(d));
    } catch (e) {
        handleError("getCurrentData", e);
    }
}

export async function getCurrentActions(context: DataItem) {
    try {
        const res = await ax_app.get(`/${context.uuid}/actions`);
        appdata.actions = (res.data['actions'] || []).map(
            (a: { name: string; uuid: string; status: number; type: string }) => ({
                name: a["name"],
                uuid: a["uuid"],
                status: statusMap.get(a['status']) || "Failed",
                type_path: a["type"]
            })
        );
    } catch (e) {
        handleError("getCurrentActions", e);
    }
}

export async function switchScenario(scenario: ScenarioItem) {
    try {
        const res = await ax_app.post("/scenarios", {
            scenario: scenario.name
        });
        if (res.status == 200) {
            scenario.name = res.data['current_scenario'];
            await Promise.all([
                fetchContextTypes(),
                fetchActionTypes(),
            ]);
            appdata.currentScenario = scenario;
            appdata.availableQuickActions = res.data['quick_actions'] || [];
        }
    } catch (e) {
        handleError("switchScenario", e);
    }
}

export async function switchContext(context: DataItem) {
    try {
        const res = await ax_app.post(`/contexts/${context.uuid}`);
        if (res.status == 200) {
            await Promise.all([
                getCurrentData(context),
                getCurrentActions(context),
                fetchActionTypes(),
            ]);
            appdata.currentContext = context;
        }
    } catch (e) {
        handleError("switchContext", e);
    }
}

export async function fetchContextTypes() {
    try {
        const res = await ax_app.get("/types/context");
        appdata.availableContextTypes = (res.data['context_types'] || []).map(
            (e: { name: string; type: string }) => ({
                type_name: e['name'],
                type_path: e['type'],
            })
        );
    } catch (e) {
        handleError("fetchContextTypes", e);
    }
}

export async function fetchActionTypes() {
    try {
        const res = await ax_app.get("/types/action");
        appdata.availableActionTypes = (res.data['action_types'] || []).map(
            (t: { name: string; type: string } | string) => {
                if (typeof t === "string") {
                    return { type_name: t, type_path: null }
                }
                return { type_name: t['name'], type_path: t['type'] }
            }
        );
    } catch (e) {
        handleError("fetchActionTypes", e);
    }
}

export async function addContext(contextType: ActionType) {
    if (appdata.contexts.find(
        (c) => (c.type_path === contextType.type_path) && (c.name === DEFAULT_NAME)
    )) {
        handleError("addContext", "Context already exists.");
        return;
    }
    try {
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
                children: [],
            });
        }
    } catch (e) {
        handleError("addContext", e);
    }
}

export async function updateContext(context: DataItem, context_config: any) {
    try {
        const res = await ax_app.put(`/contexts/${context.uuid}`, {
            context_config: context_config
        });
        if (res.status == 200) {
            context.name = context_config["name"];
        } else {
            handleError("updateContext", `Failed with status ${res.status}`);
        }
    } catch (e) {
        handleError("updateContext", e);
    }
}

export async function getContextConfig(context: DataItem) {
    try {
        const res = await ax_app.get(`/contexts/${context.uuid}`);
        return res.data['context_config'];
    } catch (e) {
        handleError("getContextConfig", e);
        throw e;
    }
}

export async function deleteContext(context: DataItem) {
    try {
        const res = await ax_app.delete(`/contexts/${context.uuid}`);
        if (res.status == 200) {
            appdata.contexts = appdata.contexts.filter((c) => c.uuid !== context.uuid);
        }
    } catch (e) {
        handleError("deleteContext", e);
    }
}

export async function addAction(context: DataItem, actionType: ActionType) {
    try {
        const res = await ax_app.post(`/${context.uuid}/actions`, {
            action_config: {
                type: actionType.type_path,
                name: actionType.type_name,
                status: 0,
            }
        });
        if (res.status == 200) {
            const new_action: ActionItem = {
                name: actionType.type_name,
                uuid: res.data['action_uuid'],
                status: "New",
                type_path: actionType.type_path,
            }
            appdata.actions.push(new_action);
            return new_action;
        }
    } catch (e) {
        handleError("addAction", e);
    }
}

export async function updateAction(context: DataItem, action: ActionItem, action_config: any) {
    const oldName = action.name;
    const oldStatus = action.status;
    action.name = action_config['name'];
    action.status = "Configured";
    try {
        const res = await ax_app.put(`/${context.uuid}/actions/${action.uuid}`, {
            action_config: action_config
        });
        if (res.status != 200) {
            action.name = oldName;
            action.status = oldStatus;
            handleError("updateAction", `Failed with status ${res.status}`);
        }
    } catch (e) {
        action.name = oldName;
        action.status = oldStatus;
        handleError("updateAction", e);
    }
}

export async function getActionConfig(context: DataItem, action: ActionItem) {
    try {
        const res = await ax_app.get(`/${context.uuid}/actions/${action.uuid}`);
        return res.data['action_config'];
    } catch (e) {
        handleError("getActionConfig", e);
        throw e;
    }
}

export async function deleteAction(context: DataItem, action: ActionItem) {
    try {
        const res = await ax_app.delete(`/${context.uuid}/actions/${action.uuid}`);
        if (res.status == 200) {
            appdata.actions = appdata.actions.filter((a) => a.uuid !== action.uuid);
        }
    } catch (e) {
        handleError("deleteAction", e);
    }
}
