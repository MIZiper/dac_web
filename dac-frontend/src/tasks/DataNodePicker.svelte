<script lang="ts">
    import {
        Button,
        Input,
        Modal,
        ModalBody,
        ModalFooter,
        ModalHeader,
    } from "@sveltestrap/sveltestrap";
    import type { TaskBaseProps } from "./TaskRouter.svelte";
    import type { DataItem } from "../schema";
    import { filterNodesByType } from "../pages/MainPageHandler.svelte";
    import { onMount } from "svelte";

    let {
        config_in,
        onTaskDone,
        availableData = [],
    }: TaskBaseProps = $props();

    let isOpen = $state(false);
    let selectedQname = $state("");

    const nodeType = config_in["_task_node_type"] as string | undefined;
    const targetKey = (config_in["_task_target_key"] as string) || "data_ref";

    const matchingNodes = $derived.by(() => {
        if (nodeType) {
            return filterNodesByType(availableData ?? [], nodeType);
        }
        const all: DataItem[] = [];
        function walk(nodes: DataItem[]) {
            for (const n of nodes) {
                if (n.qualified_name) all.push(n);
                if (n.children) walk(n.children);
            }
        }
        walk(availableData ?? []);
        return all;
    });

    const groups = $derived.by(() => {
        const map = new Map<string, DataItem[]>();
        for (const n of matchingNodes) {
            const key = n.type_path;
            if (!map.has(key)) map.set(key, []);
            map.get(key)!.push(n);
        }
        return [...map.entries()];
    });

    function onSave() {
        if (!selectedQname) return;
        isOpen = false;
        onTaskDone({ [targetKey]: selectedQname });
    }

    onMount(() => {
        isOpen = true;
    });
</script>

<Modal {isOpen} size="lg">
    <ModalHeader>Pick Data Node {nodeType ? `(${nodeType})` : ""}</ModalHeader>
    <ModalBody>
        {#if groups.length === 0}
            <p class="text-muted">No data nodes available in current context.</p>
        {:else}
            <p class="small text-muted mb-2">
                Select a node to set <code>{targetKey}</code>. Qualified name will be used.
            </p>
            <select
                class="form-select"
                bind:value={selectedQname}
                size={String(Math.min(groups.reduce((s, [, ns]) => s + ns.length, 0) + groups.length, 12))}
            >
                <option value="" disabled>-- choose a data node --</option>
                {#each groups as [typePath, nodes] (typePath)}
                    <optgroup label={typePath}>
                        {#each nodes as node (node.uuid)}
                            <option value={node.qualified_name ?? node.name}>
                                {node.qualified_name ?? node.name}
                            </option>
                        {/each}
                    </optgroup>
                {/each}
            </select>
        {/if}
    </ModalBody>
    <ModalFooter>
        <Button
            color="primary"
            onclick={onSave}
            disabled={!selectedQname}>Ok</Button
        >
        <Button
            color="secondary"
            onclick={() => {
                isOpen = false;
                onTaskDone(null);
            }}>Cancel</Button
        >
    </ModalFooter>
</Modal>
