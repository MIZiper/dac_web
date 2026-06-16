<script lang="ts">
    import { Icon } from "@sveltestrap/sveltestrap";
    import type { DataItem } from "../schema";

    let {
        datum,
        level = 0,
        collapsed,
        toggleCollapse,
        popDataMenu,
    }: {
        datum: DataItem;
        level: number;
        collapsed: Set<string>;
        toggleCollapse: (id: string) => void;
        popDataMenu: (d: DataItem, e: MouseEvent) => void;
    } = $props();

    // self import for recursion
    import DataNode from "./DataNode.svelte";
</script>

<div class="data-node" style="padding-left: {(level + 1) * 6}px;">
    {#if datum.children && datum.children.length > 0}
        <span
            role="none"
            class="arrow"
            onclick={(e) => {
                e.preventDefault();
                toggleCollapse(datum.uuid);
            }}
        >
            {#if collapsed.has(datum.uuid)}
                <Icon name="chevron-right" />
            {:else}
                <Icon name="chevron-down" />
            {/if}
        </span>
    {:else}
        <span class="arrow-placeholder"></span>
    {/if}
    <div class="data-main" role="none" onclick={(e) => popDataMenu(datum, e)}>
        <span class="data-name">{datum.name}</span>
        <span class="data-type"><code>{String(datum.type_path).split(".").slice(-1)}</code></span>
    </div>
</div>

{#if datum.children && !collapsed.has(datum.uuid)}
    {#each datum.children as child (child.uuid)}
        <DataNode
            datum={child}
            level={level + 1}
            {collapsed}
            {toggleCollapse}
            {popDataMenu}
        />
    {/each}
{/if}

<style>
    .data-node {
        display: flex;
        align-items: center;
        gap: 6px;
    }
    .arrow {
        width: 8px;
        font-size: 10px;
        cursor: pointer;
        display: inline-flex;
        align-items: center;
    }
    .arrow-placeholder {
        width: 8px;
    }
    .data-main {
        flex: 1;
        cursor: pointer;
        display: flex;
        gap: 8px;
        border-bottom: 1px dashed #666;
    }
    .data-name {
        font-size: 0.8rem;
        font-weight: bold;
    }
    .data-type {
        font-size: 0.8rem;
        color: var(--bs-secondary-text, #666);
        flex-shrink: 0;
        margin-left: auto;
        padding-right: 2px;
    }
</style>
