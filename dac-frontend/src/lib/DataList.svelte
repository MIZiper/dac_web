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

    let matchedQuickActions = $derived.by(() =>
        selectedDatum
            ? availableQuickActions.filter(
                  (qa) => qa.data_path === selectedDatum.type_path,
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
            <ListGroup flush>
                {#each data as datum (datum.uuid)}
                    <ListGroupItem
                        action
                        onclick={(e) => popDataMenu(datum, e)}
                    >
                        {datum.name}
                        <br />
                        <code>{datum.type_path.split(".").slice(-1)}</code>
                    </ListGroupItem>
                {/each}
            </ListGroup>
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
                            if (onQuickAction)
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
