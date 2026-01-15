import type { Component } from "svelte";

export interface TaskBaseProps {
    config_in: Record<string, any>,
    onTaskDone: (config_out: Record<string, any> | null) => void
}

import NameEditor from "./NameEditor.svelte";

export const taskHolder: {
    mapping: Record<string, [[string, Component<TaskBaseProps>]]>,
    defaults: Record<string, [string, Component]>,
    currentComponent: Component<TaskBaseProps> | null,
} = $state({
    mapping: {
        "dac.core.actions.Separator": [
            ["Example task", NameEditor]
        ]
    },
    defaults: {},
    currentComponent: null,
});