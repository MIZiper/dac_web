export interface DataItem {
    name: string,
    uuid: string,
    type_path: string,
    children: DataItem[],
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
    dpn: string,
    opd: any,
}

export interface ScenarioItem {
    name: string,
}
