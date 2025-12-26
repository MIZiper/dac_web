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
    import { GCK_ID } from "../utils/FetchObjects";

    let {
        contexts,
        availableContextTypes,
        currentContext,
        onSwitchContext,
        onDeleteContext = null,
        onEditContext = null,
        onAddContextType = null,
    }: {
        contexts: DataItem[];
        availableContextTypes: ActionType[];
        currentContext: DataItem | null;
        onSwitchContext: (c: DataItem) => void;
        onDeleteContext: ((c: DataItem) => void) | null;
        onEditContext: ((c: DataItem) => void) | null;
        onAddContextType: ((t: ActionType) => void) | null;
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
                        {#if currentContext && currentContext.uuid !== GCK_ID}
                            <DropdownItem
                                onclick={(e) => {
                                    if (onEditContext)
                                        onEditContext(currentContext);
                                }}>Edit</DropdownItem
                            >
                        {/if}
                        <DropdownItem disabled>Run All</DropdownItem>
                        {#if currentContext && currentContext.uuid !== GCK_ID}
                            <DropdownItem divider />
                            <DropdownItem
                                onclick={(e) => {
                                    if (onDeleteContext)
                                        onDeleteContext(currentContext);
                                }}>Delete</DropdownItem
                            >
                        {/if}
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
                            <DropdownItem
                                onclick={(e) => {
                                    if (onAddContextType)
                                        onAddContextType(contextType);
                                }}>{contextType.type_name}</DropdownItem
                            >
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
                let ctx =
                    contexts.find((c) => c.uuid === e.currentTarget.value) ||
                    null;

                if (ctx && ctx.uuid !== currentContext?.uuid) {
                    onSwitchContext(ctx);
                }
            }}
        >
            {#each contexts as context (context.uuid)}
                <option value={context.uuid}>{context.name}</option>
            {/each}
        </Input>
    </CardBody>
</Card>
