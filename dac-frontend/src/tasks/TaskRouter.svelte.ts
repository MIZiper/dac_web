import type { Component } from "svelte";
import type { DataItem } from "../schema";

export interface TaskBaseProps {
    config_in: Record<string, any>,
    onTaskDone: (config_out: Record<string, any> | null) => void,
    availableData?: DataItem[],
}

import NameEditor from "./NameEditor.svelte";
import DataNodePicker from "./DataNodePicker.svelte";

export const taskHolder: {
    mapping: Record<string, [[string, Component<TaskBaseProps>]]>,
    defaults: Record<string, [string, Component]>,
    currentComponent: Component<TaskBaseProps> | null,
} = $state({
    mapping: {
        "dac.core.actions.Separator": [
            ["Example task", NameEditor],
            ["Pick data node", DataNodePicker],
        ]
    },
    defaults: {},
    currentComponent: null,
});