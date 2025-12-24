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

    const StatusName: Map<ActionStatus, string> = new Map([
        ["New", "file-earmark-plus"],
        ["Configured", "pencil-square"],
        ["Failed", "file-earmark-x"],
        ["Completed", "file-earmark-check"],
    ]);

    let {
        actions,
        availableActionTypes,
    }: {
        actions: ActionItem[];
        availableActionTypes: ActionType[];
    } = $props();
    let isOpenActMenu = $state(false);
    function toggleActMenu() {
        isOpenActMenu = !isOpenActMenu;
    }
    let menuContainer: HTMLDivElement;

    function popActionMenu(a: ActionItem, e: MouseEvent) {
        isOpenActMenu = true;
        menuContainer.style.left = e.clientX + "px";
        menuContainer.style.top = e.clientY + "px";
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
                                    >{actionType.type_name}</DropdownItem
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
            <DropdownItem>Edit</DropdownItem>
            <DropdownItem>Run</DropdownItem>
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
