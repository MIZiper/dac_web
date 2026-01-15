<script lang="ts">
    import {
        Card,
        CardBody,
        CardHeader,
        CardTitle,
        Col,
        Dropdown,
        DropdownItem,
        DropdownMenu,
        DropdownToggle,
        Icon,
        ListGroup,
        ListGroupItem,
        Row,
    } from "@sveltestrap/sveltestrap";
    import type { ActionItem, ActionStatus, ActionType } from "../schema";
    import { taskHolder } from "../tasks/TaskRouter.svelte";

    const StatusName: Map<ActionStatus, string> = new Map([
        ["New", "file-earmark-plus"],
        ["Configured", "pencil-square"],
        ["Failed", "file-earmark-x"],
        ["Completed", "file-earmark-check"],
    ]);

    let {
        actions,
        availableActionTypes,
        onEditAction = null,
        onRunAction = null,
        onDeleteAction = null,
        onAddActionType = null,
    }: {
        actions: ActionItem[];
        availableActionTypes: ActionType[];
        onEditAction: ((a: ActionItem) => void) | null;
        onRunAction: ((a: ActionItem) => void) | null;
        onDeleteAction: ((a: ActionItem) => void) | null;
        onAddActionType: ((t: ActionType) => void) | null;
    } = $props();
    let isOpenActMenu = $state(false);
    function toggleActMenu() {
        isOpenActMenu = !isOpenActMenu;

        // this will trigger before `handleMenu`, need to find a way to set null after menu closed
        // if (!isOpenActMenu) {
        //     selectedAction = null;
        // }
    }
    let menuContainer: HTMLDivElement;
    let selectedAction: ActionItem | null = $state(null);

    function popActionMenu(a: ActionItem, e: MouseEvent) {
        isOpenActMenu = true;
        selectedAction = a;
        menuContainer.style.left = e.clientX + "px";
        menuContainer.style.top = e.clientY + "px";
    }
    function handleMenu(t: "edit" | "run" | "delete") {
        if (!selectedAction) {
            return;
        }
        if (t === "edit" && onEditAction) {
            onEditAction(selectedAction);
        } else if (t === "run" && onRunAction) {
            onRunAction(selectedAction);
        } else if (t === "delete" && onDeleteAction) {
            onDeleteAction(selectedAction);
        }
    }
</script>

<Card>
    <CardHeader>
        <Row>
            <Col>
                <CardTitle>Action</CardTitle>
            </Col>
            <Col xs="auto">
                <Dropdown>
                    <DropdownToggle caret>
                        <Icon name="plus" title="Add action" />
                    </DropdownToggle>
                    <DropdownMenu>
                        {#each availableActionTypes as actionType}
                            {#if actionType.type_path === null}
                                {#if actionType.type_name.endsWith(">]")}
                                    <DropdownItem divider />
                                    <DropdownItem header
                                        >{actionType.type_name.slice(
                                            1,
                                            -2,
                                        )}</DropdownItem
                                    >
                                {:else if actionType.type_name.endsWith("<]")}
                                    <DropdownItem divider />
                                {:else}
                                    <DropdownItem header
                                        >{actionType.type_name.slice(
                                            1,
                                            -1,
                                        )}</DropdownItem
                                    >
                                {/if}
                            {:else}
                                <DropdownItem
                                    onclick={(e) => {
                                        if (onAddActionType)
                                            onAddActionType(actionType);
                                    }}>{actionType.type_name}</DropdownItem
                                >
                            {/if}
                        {/each}
                    </DropdownMenu>
                </Dropdown>
            </Col>
        </Row>
    </CardHeader>
    <CardBody class="p-0">
        <div class="list-scroll">
            <ListGroup flush>
                {#each actions as action (action.uuid)}
                    <ListGroupItem
                        action
                        onclick={(e) => popActionMenu(action, e)}
                    >
                        <Icon
                            name={StatusName.get(action.status) ||
                                "question-circle"}
                        ></Icon>
                        {action.name}
                    </ListGroupItem>
                {/each}
            </ListGroup>
        </div>
    </CardBody>
</Card>

<div bind:this={menuContainer} style="position: fixed; z-index: 9;">
    <Dropdown isOpen={isOpenActMenu} toggle={toggleActMenu}>
        <DropdownMenu>
            {#if selectedAction && taskHolder.mapping[selectedAction.name]} <!-- not .name but .type_path -->
                {#each taskHolder.mapping[selectedAction.name] as task}
                    <DropdownItem
                        onclick={() => {
                            taskHolder.currentComponent = task[1];
                        }}>{task[0]}</DropdownItem
                    >
                {/each}
                <DropdownItem divider />
            {/if}
            <DropdownItem onclick={(e) => handleMenu("edit")}>Edit</DropdownItem
            >
            <DropdownItem onclick={(e) => handleMenu("run")}>Run</DropdownItem>
            <DropdownItem divider />
            <DropdownItem onclick={(e) => handleMenu("delete")}
                >Delete</DropdownItem
            >
        </DropdownMenu>
    </Dropdown>
</div>

<style>
    .list-scroll {
        height: 400px;
        overflow-y: auto;
    }
</style>
