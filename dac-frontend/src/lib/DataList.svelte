<script lang="ts">
    import {
        Button,
        Card,
        CardBody,
        CardHeader,
        CardTitle,
        Col,
        Dropdown,
        DropdownItem,
        DropdownMenu,
        Icon,
        ListGroup,
        ListGroupItem,
        Row,
    } from "@sveltestrap/sveltestrap";
    import type { DataItem, DataQuickAction } from "../schema";
    import DataNode from "./DataNode.svelte";

    let {
        data,
        availableQuickActions,
        onQuickAction = null,
    }: {
        data: DataItem[];
        availableQuickActions: DataQuickAction[];
        onQuickAction: ((d: DataItem, q: DataQuickAction) => void) | null;
    } = $props();

    let isOpenDatMenu = $state(false);
    function toggleDatMenu() {
        isOpenDatMenu = !isOpenDatMenu;
    }
    let menuContainer: HTMLDivElement;
    let selectedDatum: DataItem | null = $state(null);

    // collapsed set holds uuids that are collapsed
    let collapsed: Set<string> = $state(new Set());
    function toggleCollapse(id: string) {
        if (collapsed.has(id)) {
            collapsed.delete(id);
            collapsed = new Set(collapsed);
        } else {
            collapsed.add(id);
            collapsed = new Set(collapsed);
        }
    }

    let matchedQuickActions = $derived.by(() =>
        selectedDatum
            ? availableQuickActions.filter(
                  (qa) => qa.data_path === (selectedDatum as DataItem).type_path,
              )
            : [],
    );

    function popDataMenu(d: DataItem, e: MouseEvent) {
        isOpenDatMenu = true;
        selectedDatum = d;
        menuContainer.style.left = e.clientX + "px";
        menuContainer.style.top = e.clientY + "px";
    }
    function handleMenu(t: "delete") {
        if (!selectedDatum) {
            return;
        }
    }
</script>

<Card>
    <CardHeader>
        <Row>
            <Col>
                <CardTitle>Data</CardTitle>
            </Col>
            <Col xs="auto">
                <Button><Icon name="trash" /></Button>
            </Col>
        </Row>
    </CardHeader>
    <CardBody class="p-0">
        <div class="list-scroll">
            {#if data}
                {#each data as datum (datum.uuid)}
                    <DataNode
                        {datum}
                        level={0}
                        {collapsed}
                        {toggleCollapse}
                        {popDataMenu}
                    />
                {/each}
            {/if}
        </div>
    </CardBody>
</Card>

<div bind:this={menuContainer} style="position: fixed; z-index: 9;">
    <Dropdown isOpen={isOpenDatMenu} toggle={toggleDatMenu}>
        <DropdownMenu>
            {#if selectedDatum}
                {#each matchedQuickActions as quickAction}
                    <DropdownItem
                        onclick={(e) => {
                            if (onQuickAction && selectedDatum)
                                onQuickAction(selectedDatum, quickAction);
                        }}>{quickAction.action_name}</DropdownItem
                    >
                {/each}
                {#if matchedQuickActions.length > 0}
                    <DropdownItem divider />
                {/if}
            {/if}
            <DropdownItem disabled>Delete</DropdownItem>
        </DropdownMenu>
    </Dropdown>
</div>

<style>
    .list-scroll {
        height: 400px;
        overflow-y: auto;
    }
</style>
