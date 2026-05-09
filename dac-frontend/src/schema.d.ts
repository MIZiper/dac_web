export interface DataItem {
    name: string,
    uuid: string,
    type_path: string,
    children?: DataItem[],
}

export type ActionStatus = "New" | "Configured" | "Completed" | "Failed";

export interface ActionItem {
    name: string,
    uuid: string,
    status: ActionStatus,
    type_path: string,
}

export interface ActionType {
    type_name: string;
    type_path: string;
}

export interface DataQuickAction {
    data_path: string,
    action_name: string,
    action_path: string,
    idx: number,
}

export interface ScenarioItem {
    name: string,
}

export enum ActionStatusNum {
    New = 0,
    Configured = 1,
    Completed = 2,
    Failed = -1,
}

export interface ContextMeta {
    name: string;
    uuid: string;
    type: string;
}

export interface ScenariosResponse {
    message: string;
    scenarios: string[];
    current_scenario: string;
    quick_actions?: DataQuickAction[];
}

export interface ContextsResponse {
    message: string;
    contexts: ContextMeta[];
    current_context: string;
}

export interface ContextCreateResponse {
    message: string;
    context_uuid: string;
}

export interface TypesResponse {
    message: string;
    context_types?: Array<{ name: string; type: string } | string>;
    action_types?: Array<{ name: string; type: string } | string>;
}

export interface DataResponse {
    message: string;
    data: Array<{
        name: string;
        uuid: string;
        type: string;
        children: any[];
    }>;
}

export interface ActionsResponse {
    message: string;
    actions: Array<{
        name: string;
        uuid: string;
        status: number;
        type: string;
    }>;
}

export interface ActionCreateResponse {
    message: string;
    action_uuid: string;
}

export interface NodeConfig {
    name: string;
    [key: string]: any;
}

export interface ContextExchange {
    context_config: NodeConfig;
}

export interface ActionExchange {
    action_config: NodeConfig;
}

export interface ProjectItem {
    id: string;
    created_at: string;
    updated_at: string;
    title: string | null;
    creator_name: string | null;
}

export interface ProjectListResponse {
    message: string;
    projects: ProjectItem[];
    total: number;
    page: number;
    page_size: number;
}
