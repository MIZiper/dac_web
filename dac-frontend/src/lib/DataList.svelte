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
    import type { DataItem } from "../schema";

    let data: DataItem[] = $state([
        { name: "Dat 1", uuid: "xxx", type_path: "a.b.c" },
        { name: "Dat 2", uuid: "yyy", type_path: "d.e.f" },
        { name: "Dat 3", uuid: "zzz", type_path: "g.h.i" },
    ]);
    let isOpenDatMenu = $state(false);
    function toggleDatMenu() {
        isOpenDatMenu = !isOpenDatMenu;
    }
    let menuContainer: HTMLDivElement;

    function popDataMenu(d: DataItem, e: MouseEvent) {
        isOpenDatMenu = true;
        menuContainer.style.left = e.clientX + "px";
        menuContainer.style.top = e.clientY + "px";
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
                    </ListGroupItem>
                {/each}
            </ListGroup>
        </div>
    </CardBody>
</Card>

<div bind:this={menuContainer} style="position: fixed; z-index: 9;">
    <Dropdown isOpen={isOpenDatMenu} toggle={toggleDatMenu}>
        <DropdownMenu>
            <DropdownItem>View</DropdownItem>
            <DropdownItem>Custom ...</DropdownItem>
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
