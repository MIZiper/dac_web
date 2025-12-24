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
    import type { ActionType, DataItem } from "../schema";

    let {
        contexts,
        availableContextTypes,
        currentContext = $bindable(),
    }: {
        contexts: DataItem[];
        availableContextTypes: ActionType[];
        currentContext: DataItem | null;
    } = $props();
</script>

<Card>
    <CardHeader>
        <Row>
            <Col>
                <CardTitle>Context</CardTitle>
            </Col>
            <Col xs="auto" class="pe-1">
                <Dropdown>
                    <DropdownToggle caret>
                        <Icon name="three-dots-vertical" title="Context menu" />
                    </DropdownToggle>
                    <DropdownMenu>
                        <DropdownItem>Run</DropdownItem>
                    </DropdownMenu>
                </Dropdown>
            </Col>
            <Col xs="auto" class="ps-1">
                <Dropdown>
                    <DropdownToggle caret>
                        <Icon name="plus" title="Add context data" />
                    </DropdownToggle>
                    <DropdownMenu>
                        {#each availableContextTypes as contextType}
                            <DropdownItem>{contextType.type_name}</DropdownItem>
                        {/each}
                    </DropdownMenu>
                </Dropdown>
            </Col>
        </Row>
    </CardHeader>
    <CardBody>
        <Input
            type="select"
            value={currentContext?.uuid}
            onchange={(e) => {
                currentContext =
                    contexts.find((c) => c.uuid === e.currentTarget.value) ||
                    null;
            }}
        >
            {#each contexts as context (context.uuid)}
                <option value={context.uuid}>{context.name}</option>
            {/each}
        </Input>
    </CardBody>
</Card>
