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
    import type { ActionItem } from "../schema";

    let actions: ActionItem[] = $state([]);
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
                        <Icon name="plus" />
                    </DropdownToggle>
                    <DropdownMenu>
                        <DropdownItem>Add action</DropdownItem>
                    </DropdownMenu>
                </Dropdown>
            </Col>
        </Row>
    </CardHeader>
    <CardBody>
        <ListGroup>
            {#each actions as action (action.uuid)}
                <ListGroupItem>
                    <Icon name=""></Icon>
                    {action.name}
                </ListGroupItem>
            {/each}
        </ListGroup>
    </CardBody>
</Card>
