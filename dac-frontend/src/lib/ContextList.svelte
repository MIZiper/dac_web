<script lang="ts">
    import {
        ButtonGroup,
        Card,
        CardBody,
        CardFooter,
        CardHeader,
        CardTitle,
        Col,
        Dropdown,
        DropdownItem,
        DropdownMenu,
        DropdownToggle,
        Icon,
        Input,
        Row,
    } from "@sveltestrap/sveltestrap";
    import type { DataItem } from "../schema";

    let contexts: DataItem[] = $state([]);
</script>

<Card>
    <CardHeader>
        <Row>
            <Col>
                <CardTitle>Context</CardTitle>
            </Col>
            <Col xs="auto">
                <Dropdown>
                    <DropdownToggle caret>
                        <Icon name="three-dots-vertical" />
                    </DropdownToggle>
                    <DropdownMenu>
                        <DropdownItem>Run</DropdownItem>
                    </DropdownMenu>
                </Dropdown>
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
        <Input type="select">
            {#each contexts as context (context.uuid)}
                <option>{context.name}</option>
            {/each}
        </Input>
    </CardBody>
</Card>
