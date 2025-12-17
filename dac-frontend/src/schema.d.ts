export interface DataItem {
    name: string,
    uuid: string,
    type_path: string,
}

export type ActionStatus = "New" | "Configured" | "Completed" | "Failed";

export interface ActionItem {
    name: string,
    uuid: string,
    status: ActionStatus,
}

export interface ActionType {
    type_name: string;
    type_path: string;
}

